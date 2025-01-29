from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import json
import numpy as np
import os
from colorthief import ColorThief

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

with open('themes.json') as f:
    themes = json.load(f)['themes']

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(*rgb)

def extract_colors(image_path):
    cf = ColorThief(image_path)
    palette = cf.get_palette(color_count=6, quality=1)
    return [rgb_to_hex(color) for color in palette]

def color_similarity(color1, color2):
    r1, g1, b1 = tuple(int(color1[i:i+2], 16) for i in (1, 3, 5))
    r2, g2, b2 = tuple(int(color2[i:i+2], 16) for i in (1, 3, 5))
    return np.sqrt((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2)

def find_theme(image_colors):
    best_theme = None
    min_score = float('inf')
    
    for theme in themes:
        score = 0
        theme_colors = theme['colors'].values()
        for img_color in image_colors:
            scores = [color_similarity(img_color, t_color) for t_color in theme_colors]
            score += min(scores)
        
        if score < min_score:
            min_score = score
            best_theme = theme['name']
    
    return best_theme

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/detect', methods=['POST'])
def detect_theme():
    if 'file' not in request.files:
        return jsonify(error="No file uploaded"), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify(error="No selected file"), 400

    temp_path = None  # Track the temporary file path
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        if not os.path.exists(temp_path):
            return jsonify(error="Failed to save file"), 500

        image_colors = extract_colors(temp_path)
        theme = find_theme(image_colors)
        
        return jsonify(theme=theme, colors=image_colors)

    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify(error=f"Processing error: {str(e)}"), 500

    finally:
        # Clean up the temporary file after processing
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as cleanup_error:
                app.logger.error(f"Failed to clean up file: {str(cleanup_error)}")

if __name__ == '__main__':
    app.run(debug=True)