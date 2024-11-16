from PIL import Image
from flask import Flask, request, send_file, render_template, redirect, url_for
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

def convert_image(input_path, output_path):
    # Open an image file
    with Image.open(input_path) as img:
        # Convert the image to 1024x1024 using LANCZOS for high-quality downsampling
        img = img.resize((1024, 1024), Image.LANCZOS)
        # Save it to the output path
        img.save(output_path)

@app.route('/', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return "No file part in the request"
        file = request.files['file']
        if file.filename == '':
            return "No selected file"
        if file:
            input_image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(input_image_path)
            
            # Convert the uploaded image
            output_image_path = os.path.join(app.config['OUTPUT_FOLDER'], 'converted_image.png')
            convert_image(input_image_path, output_image_path)
            
            return redirect(url_for('download_image', filename='converted_image.png'))
    return '''
    <!doctype html>
    <title>Apple AppStore Icon Converter</title>
    <h1>Automatically changes any picture into 1024x1024 which XCode supports... just hit Convert</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Convert>
    </form>
    '''

@app.route('/download/<filename>')
def download_image(filename):
    output_image_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    return send_file(output_image_path, mimetype='image/png', as_attachment=True)

if __name__ == '__main__':
    # Run the Flask server
    app.run(host='0.0.0.0', port=829)
