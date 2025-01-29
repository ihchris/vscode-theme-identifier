from flask import Flask, request, render_template, jsonify
from PIL import Image
import json
import numpy as np
import os
from colorthief import ColorThief

app = Flask(__name__)

# Load theme database
with open('themes.json') as f:
    themes = json.load(f)['themes']

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(*rgb)

def extract_colors(image_path):
    cf = ColorThief(image_path)
    palette = cf.get_palette(color_count=6, quality=1)
    return [rgb_to_hex(color) for color in palette]

def color_similarity(color1, color2):
    # Convert hex to RGB
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
    
    try:
        temp_path = os.path.join('static', 'uploads', file.filename)
        file.save(temp_path)
        
        # Extract colors
        image_colors = extract_colors(temp_path)
        
        # Find matching theme
        theme = find_theme(image_colors)
        
        return jsonify(theme=theme, colors=image_colors)
        
    except Exception as e:
        return jsonify(error=str(e)), 500

if __name__ == '__main__':
    os.makedirs(os.path.join('static', 'uploads'), exist_ok=True)
    app.run(debug=True)