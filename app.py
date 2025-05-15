import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
import time
import json
import csv
from pathlib import Path
import tempfile

# Import our custom modules
from tools.file_processors.processor_factory import get_processor
from tools.geo_helpers import geojson_helper, polygon_helper
from tools.api import (
    get_businesses,
    get_consumers,
    get_complete_area_insights,
    calculate_affluence_score
)
from tools.utils.file_utils import ensure_directory_exists, safe_json_write
from tools.utils.date_utils import get_current_datetime_string

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your_secret_key")  # Replace with a secure key in production

# Configure application
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['ALLOWED_EXTENSIONS'] = {'kmz', 'kml'}
app.config['LATEST_PROCESSED_GEOJSON'] = None
app.config['ACTIVE_WORKFLOW'] = None  # 'business', 'consumer', or 'insights'

# Create folders if they don't exist
ensure_directory_exists(app.config['UPLOAD_FOLDER'])
ensure_directory_exists(app.config['OUTPUT_FOLDER'])


def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing."""
    # Check if a file was submitted
    if 'geo_file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})

    file = request.files['geo_file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Get the appropriate processor based on file extension
        file_type = filename.rsplit('.', 1)[1].lower()
        processor = get_processor(file_type)

        # Define output paths
        geojson_output = os.path.join(app.config['OUTPUT_FOLDER'], f"{filename.rsplit('.', 1)[0]}.geojson")
        processed_geojson = os.path.join(app.config['OUTPUT_FOLDER'], f"{filename.rsplit('.', 1)[0]}_processed.geojson")

        try:
            # Process the file
            processor.process_file(file_path, geojson_output)

            # Further process the geojson (e.g., simplify polygons)
            max_points = 500
            polygon_helper.process_geojson(geojson_output, processed_geojson, max_points)

            # Parse the processed geojson
            polygon_data = geojson_helper.parse_geojson(processed_geojson)

            # Store the path to the processed file
            app.config['LATEST_PROCESSED_GEOJSON'] = processed_geojson

            return jsonify({
                'success': True,
                'message': f'File {filename} uploaded and processed successfully!',
                'filename': filename,
                'polygon_count': len(polygon_data)
            })

        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Error processing file: {str(e)}'
            }), 500
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid file type. Please upload a KMZ or KML file.'
        })


@app.route('/get_folders', methods=['GET'])
def get_folders():
    """Get all folders from the processed file."""
    latest_file = app.config['LATEST_PROCESSED_GEOJSON']

    if not latest_file or not os.path.exists(latest_file):
        return jsonify({
            'success': False,
            'message': 'No processed GeoJSON file found. Please upload a file first.'
        }), 404

    try:
        folders = geojson_helper.get_folders_in_geojson(latest_file)
        return jsonify({
            'success': True,
            'folders': folders
        })
    except Exception as e:
        logger.error(f"Error retrieving folders: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error retrieving folders: {str(e)}'
        }), 500


@app.route('/set_workflow', methods=['POST'])
def set_workflow():
    """Set the active workflow."""
    workflow = request.json.get('workflow')
    if workflow not in ['business', 'consumer', 'insights']:
        return jsonify({
            'success': False,
            'message': 'Invalid workflow selected'
        }), 400

    app.config['ACTIVE_WORKFLOW'] = workflow
    return jsonify({
        'success': True,
        'message': f'Workflow set to {workflow}'
    })


@app.route('/get_businesses', methods=['POST'])
def get_businesses_route():
    """Get businesses for selected folders."""
    folders = request.json.get('folders', [])
    if not folders:
        return jsonify({
            'success': False,
            'message': 'No folders selected'
        }), 400

    latest_file = app.config['LATEST_PROCESSED_GEOJSON']
    if not latest_file or not os.path.exists(latest_file):
        return jsonify({
            'success': False,
            'message': 'No processed file found. Please upload a file first.'
        }), 404

    try:
        # Parse the processed geojson
        polygon_data = geojson_helper.parse_geojson(latest_file)

        # Filter polygons by selected folders
        selected_polygons = [p for p in polygon_data if p.get('folder') in folders]

        if not selected_polygons:
            return jsonify({
                'success': False,
                'message': 'No polygons found in the selected folders'
            }), 404

        # Get businesses for each polygon
        all_businesses = []
        for polygon in selected_polygons:
            businesses = get_businesses(polygon['points'])
            for business in businesses:
                # Add source polygon info to each business record
                business['source_polygon'] = polygon['name']
                business['source_folder'] = polygon['folder']

            all_businesses.extend(businesses)

        return jsonify({
            'success': True,
            'businesses': all_businesses,
            'count': len(all_businesses)
        })
    except Exception as e:
        logger.error(f"Error getting businesses: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error getting businesses: {str(e)}'
        }), 500


@app.route('/get_consumers', methods=['POST'])
def get_consumers_route():
    """Get consumers for selected folders."""
    folders = request.json.get('folders', [])
    head_of_household = request.json.get('head_of_household', True)

    if not folders:
        return jsonify({
            'success': False,
            'message': 'No folders selected'
        }), 400

    latest_file = app.config['LATEST_PROCESSED_GEOJSON']
    if not latest_file or not os.path.exists(latest_file):
        return jsonify({
            'success': False,
            'message': 'No processed file found. Please upload a file first.'
        }), 404

    try:
        # Parse the processed geojson
        polygon_data = geojson_helper.parse_geojson(latest_file)

        # Filter polygons by selected folders
        selected_polygons = [p for p in polygon_data if p.get('folder') in folders]

        if not selected_polygons:
            return jsonify({
                'success': False,
                'message': 'No polygons found in the selected folders'
            }), 404

        # Get consumers for each polygon
        all_consumers = []
        for polygon in selected_polygons:
            consumers = get_consumers(polygon['points'], head_of_household=head_of_household)
            for consumer in consumers:
                # Add source polygon info to each consumer record
                consumer['source_polygon'] = polygon['name']
                consumer['source_folder'] = polygon['folder']

            all_consumers.extend(consumers)

        return jsonify({
            'success': True,
            'consumers': all_consumers,
            'count': len(all_consumers)
        })
    except Exception as e:
        logger.error(f"Error getting consumers: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error getting consumers: {str(e)}'
        }), 500


@app.route('/get_insights', methods=['POST'])
def get_insights_route():
    """Get insights for selected folders."""
    folders = request.json.get('folders', [])

    if not folders:
        return jsonify({
            'success': False,
            'message': 'No folders selected'
        }), 400

    latest_file = app.config['LATEST_PROCESSED_GEOJSON']
    if not latest_file or not os.path.exists(latest_file):
        return jsonify({
            'success': False,
            'message': 'No processed file found. Please upload a file first.'
        }), 404

    try:
        # Parse the processed geojson
        polygon_data = geojson_helper.parse_geojson(latest_file)

        # Filter polygons by selected folders
        selected_polygons = [p for p in polygon_data if p.get('folder') in folders]

        if not selected_polygons:
            return jsonify({
                'success': False,
                'message': 'No polygons found in the selected folders'
            }), 404

        # Get insights for each polygon
        results = []
        for polygon in selected_polygons:
            insights = get_complete_area_insights(polygon['points'])

            # Calculate affluence score
            affluence_score = calculate_affluence_score(polygon['points'])

            # Add to results
            results.append({
                'polygon_name': polygon['name'],
                'folder': polygon['folder'],
                'affluence_score': affluence_score,
                'insights': insights
            })

        return jsonify({
            'success': True,
            'insights': results
        })
    except Exception as e:
        logger.error(f"Error getting insights: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error getting insights: {str(e)}'
        }), 500


@app.route('/export_businesses_csv', methods=['POST'])
def export_businesses_csv():
    """Export businesses to CSV."""
    businesses = request.json.get('businesses', [])

    if not businesses:
        return jsonify({
            'success': False,
            'message': 'No businesses to export'
        }), 400

    try:
        # Create a temporary file
        fd, temp_path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)

        # Determine fieldnames from the first business
        fieldnames = list(businesses[0].keys())

        # Write the CSV
        with open(temp_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(businesses)

        # Generate a download filename
        timestamp = get_current_datetime_string()
        download_filename = f"businesses_{timestamp}.csv"

        return send_file(
            temp_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype='text/csv'
        )
    except Exception as e:
        logger.error(f"Error exporting businesses to CSV: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error exporting businesses to CSV: {str(e)}'
        }), 500


@app.route('/export_consumers_csv', methods=['POST'])
def export_consumers_csv():
    """Export consumers to CSV."""
    consumers = request.json.get('consumers', [])

    if not consumers:
        return jsonify({
            'success': False,
            'message': 'No consumers to export'
        }), 400

    try:
        # Create a temporary file
        fd, temp_path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)

        # Determine fieldnames from the first consumer
        fieldnames = list(consumers[0].keys())

        # Write the CSV
        with open(temp_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(consumers)

        # Generate a download filename
        timestamp = get_current_datetime_string()
        download_filename = f"consumers_{timestamp}.csv"

        return send_file(
            temp_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype='text/csv'
        )
    except Exception as e:
        logger.error(f"Error exporting consumers to CSV: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error exporting consumers to CSV: {str(e)}'
        }), 500


@app.route('/export_insights_csv', methods=['POST'])
def export_insights_csv():
    """Export insights to CSV."""
    insights_data = request.json.get('insights', [])

    if not insights_data:
        return jsonify({
            'success': False,
            'message': 'No insights to export'
        }), 400

    try:
        # Create a temporary file
        fd, temp_path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)

        # Flatten the insights data for CSV export
        flattened_data = []
        for item in insights_data:
            flat_item = {
                'polygon_name': item['polygon_name'],
                'folder': item['folder'],
                'affluence_score': item['affluence_score'],
                'household_count': item['insights'].get('household_count', 0),
                'business_count': item['insights'].get('business_count', 0)
            }

            # Add income distribution if available
            income_dist = item['insights'].get('income_distribution', {})
            if income_dist and 'insights' in income_dist and 'frequencies' in income_dist['insights']:
                for freq in income_dist['insights']['frequencies']:
                    range_name = f"income_{freq.get('lower', 0)}_{freq.get('upper', 'plus')}"
                    flat_item[range_name] = freq.get('count', 0)

            # Add home ownership if available
            home_ownership = item['insights'].get('home_ownership_rate', {})
            if home_ownership and 'insights' in home_ownership and 'frequencies' in home_ownership['insights']:
                for freq in home_ownership['insights']['frequencies']:
                    if freq.get('value') is True:
                        flat_item['home_owners'] = freq.get('count', 0)
                    elif freq.get('value') is False:
                        flat_item['non_home_owners'] = freq.get('count', 0)

            flattened_data.append(flat_item)

        # Determine fieldnames from all flattened items
        all_keys = set()
        for item in flattened_data:
            all_keys.update(item.keys())
        fieldnames = sorted(list(all_keys))

        # Write the CSV
        with open(temp_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flattened_data)

        # Generate a download filename
        timestamp = get_current_datetime_string()
        download_filename = f"insights_{timestamp}.csv"

        return send_file(
            temp_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype='text/csv'
        )
    except Exception as e:
        logger.error(f"Error exporting insights to CSV: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error exporting insights to CSV: {str(e)}'
        }), 500


@app.route('/export_kml', methods=['POST'])
def export_kml():
    """Export data to KML format."""
    workflow = request.json.get('workflow')
    data = request.json.get('data', [])

    if not data:
        return jsonify({
            'success': False,
            'message': 'No data to export'
        }), 400

    try:
        # Create a temporary file
        fd, temp_path = tempfile.mkstemp(suffix='.kml')
        os.close(fd)

        import simplekml
        kml = simplekml.Kml()

        if workflow == 'business':
            # Export businesses to KML
            for business in data:
                # Create a placemark for each business
                if 'latitude' in business and 'longitude' in business and business['latitude'] and business[
                    'longitude']:
                    # Make a point placemark
                    pnt = kml.newpoint(name=business.get('name', 'Business'))
                    pnt.coords = [(business['longitude'], business['latitude'])]

                    # Add description with business details
                    description = f"<h3>{business.get('name', 'Business')}</h3>"
                    description += f"<p>{business.get('street', '')}, {business.get('city', '')}, {business.get('state', '')} {business.get('postal_code', '')}</p>"

                    if 'phone' in business and business['phone']:
                        description += f"<p>Phone: {business['phone']}</p>"

                    if 'website' in business and business['website']:
                        description += f"<p>Website: <a href='{business['website']}'>{business['website']}</a></p>"

                    description += f"<p>Source: {business.get('source_polygon', '')} ({business.get('source_folder', '')})</p>"

                    pnt.description = description

                    # Style the point
                    pnt.style.iconstyle.color = simplekml.Color.blue
                    pnt.style.iconstyle.scale = 1.0

        elif workflow == 'consumer':
            # Export consumers to KML
            for consumer in data:
                # Create a placemark for each consumer
                if 'latitude' in consumer and 'longitude' in consumer and consumer['latitude'] and consumer[
                    'longitude']:
                    # Make a point placemark
                    pnt = kml.newpoint(name=consumer.get('name', 'Consumer'))
                    pnt.coords = [(consumer['longitude'], consumer['latitude'])]

                    # Add description with consumer details
                    description = f"<h3>{consumer.get('name', 'Consumer')}</h3>"
                    description += f"<p>{consumer.get('street', '')}, {consumer.get('city', '')}, {consumer.get('state', '')} {consumer.get('postal_code', '')}</p>"

                    if 'family' in consumer and consumer['family'] and isinstance(consumer['family'], dict):
                        if 'estimated_income_range' in consumer['family']:
                            income = consumer['family']['estimated_income_range']
                            if isinstance(income, dict) and 'lower' in income and 'upper' in income:
                                description += f"<p>Income Range: ${income['lower']} - ${income['upper']}</p>"

                    description += f"<p>Source: {consumer.get('source_polygon', '')} ({consumer.get('source_folder', '')})</p>"

                    pnt.description = description

                    # Style the point
                    pnt.style.iconstyle.color = simplekml.Color.green
                    pnt.style.iconstyle.scale = 1.0

        elif workflow == 'insights':
            # Export insights to KML
            for insight in data:
                # Create a folder for each polygon
                folder = kml.newfolder(name=f"{insight['polygon_name']} ({insight['folder']})")

                # Add a description with key metrics
                description = f"<h3>{insight['polygon_name']}</h3>"
                description += f"<p><strong>Folder:</strong> {insight['folder']}</p>"
                description += f"<p><strong>Affluence Score:</strong> {insight['affluence_score']}</p>"

                # Add key insights
                if 'insights' in insight and insight['insights']:
                    description += f"<p><strong>Household Count:</strong> {insight['insights'].get('household_count', 0)}</p>"
                    description += f"<p><strong>Business Count:</strong> {insight['insights'].get('business_count', 0)}</p>"

                folder.description = description

                # Create a placemark with style based on the affluence score
                pnt = folder.newpoint(name=insight['polygon_name'])

                # If we have a polygon geometry, we could add it here
                # For now, just add a point at the centroid of the area if available
                # This would need to be enhanced with actual polygon data

                # Style based on affluence score
                score = insight['affluence_score']
                # Color from red (low) to green (high)
                r = max(0, min(255, int(255 * (1 - score / 100))))
                g = max(0, min(255, int(255 * (score / 100))))
                color = simplekml.Color.rgb(r, g, 0)

                pnt.style.iconstyle.color = color
                pnt.style.iconstyle.scale = 1.5

        # Save the KML file
        kml.save(temp_path)

        # Generate a download filename
        timestamp = get_current_datetime_string()
        download_filename = f"{workflow}_export_{timestamp}.kml"

        return send_file(
            temp_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype='application/vnd.google-earth.kml+xml'
        )
    except Exception as e:
        logger.error(f"Error exporting to KML: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error exporting to KML: {str(e)}'
        }), 500


if __name__ == '__main__':
    app.run(debug=True)
