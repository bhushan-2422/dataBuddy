from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import numpy as np
from datetime import datetime
import json
import io
import os

app = Flask(__name__, 
            template_folder='.',  # Look for templates in current directory
            static_folder='.')     # Look for static files in current directory

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/style.css')
def serve_css():
    return send_file('style.css', mimetype='text/css')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Read CSV file
        df = pd.read_csv(file)
        
        # Handle missing values
        df = df.fillna(0)
        
        # Convert Date column to datetime
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Month'] = df['Date'].dt.strftime('%B %Y')
        
        # Compute 14 metrics
        metrics = {
            'total_sales': float(df['Sales'].sum()),
            'average_sales': float(df['Sales'].mean()),
            'total_profit': float(df['Profit'].sum()),
            'average_profit': float(df['Profit'].mean()),
            'top_selling_product': df.groupby('Product')['Quantity'].sum().idxmax(),
            'number_of_products': int(df['Product'].nunique()),
            'unique_customers': int(df['Customer'].nunique()),
            'highest_transaction': float(df['Sales'].max()),
            'lowest_transaction': float(df['Sales'].min()),
            'average_quantity': float(df['Quantity'].mean()),
            'total_orders': int(len(df)),
            'most_frequent_category': df['Category'].mode()[0] if not df['Category'].empty else 'N/A',
            'most_profitable_region': df.groupby('Region')['Profit'].sum().idxmax(),
            'month_highest_sales': df.groupby('Month')['Sales'].sum().idxmax(),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Sales by Category for charts
        sales_by_category = df.groupby('Category')['Sales'].sum().to_dict()
        profit_by_month = df.groupby('Month')['Profit'].sum().to_dict()
        sales_by_month = df.groupby('Month')['Sales'].sum().to_dict()
        
        # Store analysis for download
        global analysis_data
        analysis_data = {
            'metrics': metrics,
            'sales_by_category': sales_by_category,
            'profit_by_month': profit_by_month,
            'sales_by_month': sales_by_month,
            'raw_data': df.to_dict('records')
        }
        
        return jsonify({
            'metrics': metrics,
            'sales_by_category': sales_by_category,
            'profit_by_month': profit_by_month,
            'sales_by_month': sales_by_month
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/results')
def results():
    return render_template('results.html')

@app.route('/download_report')
def download_report():
    report_type = request.args.get('type', 'json')
    
    if report_type == 'csv':
        # Create CSV report
        df = pd.DataFrame([analysis_data['metrics']])
        output = io.BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'analysis_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    else:
        # Create JSON report
        output = io.BytesIO()
        output.write(json.dumps(analysis_data, indent=2).encode('utf-8'))
        output.seek(0)
        return send_file(
            output,
            mimetype='application/json',
            as_attachment=True,
            download_name=f'analysis_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )

if __name__ == '__main__':
    app.run(debug=True)