from PIL import Image, ImageFilter, ImageFont, ImageDraw
from flask import Flask, request, send_file, render_template, redirect, url_for, flash, send_from_directory
import os
import logging
import io
import zipfile

app = Flask(__name__)
app.secret_key = 'replace-with-your-secret-key'  # Use a secure random key in production

# Configure folders
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_image(input_path, output_path, size=(1024, 1024)):
    """
    Converts the uploaded image to the given size PNG using high-quality resampling.
    """
    try:
        with Image.open(input_path) as img:
            img = img.resize(size, Image.LANCZOS)
            img.save(output_path, format='PNG')
        return True
    except Exception as e:
        logger.error(f"Error converting image: {e}")
        return False

def generate_ios_app_icons(input_path):
    """
    Generates a set of iOS app icons from a single input image.
    Common sizes (as of iOS App Icon guidelines):
    20x20 (@1x, @2x, @3x)
    29x29 (@1x, @2x, @3x)
    40x40 (@1x, @2x, @3x)
    60x60 (@2x, @3x)
    76x76 (@1x, @2x)
    83.5x83.5 (@2x)
    1024x1024 (App Store)
    """
    sizes = [
        (20, 1), (20, 2), (20, 3),
        (29, 1), (29, 2), (29, 3),
        (40, 1), (40, 2), (40, 3),
        (60, 2), (60, 3),
        (76, 1), (76, 2),
        (83.5, 2),
        (1024, 1) # App Store
    ]

    icon_paths = []
    try:
        with Image.open(input_path) as img:
            for base_size, scale in sizes:
                output_size = (int(base_size * scale), int(base_size * scale))
                icon_img = img.resize(output_size, Image.LANCZOS)
                # Sanitize filename
                filename = f"icon_{base_size}x{base_size}@{scale}x.png".replace('.5', 'p5') 
                output_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
                icon_img.save(output_path, format='PNG')
                icon_paths.append(output_path)
    except Exception as e:
        logger.error(f"Error generating iOS app icons: {e}")
        return None
    return icon_paths

def apply_filter_to_image(input_path, filter_type):
    """
    Apply different filters to the image.
    """
    try:
        with Image.open(input_path) as img:
            if filter_type == 'grayscale':
                img = img.convert('L').convert('RGBA')
            elif filter_type == 'blur':
                img = img.filter(ImageFilter.GaussianBlur(5))
            # Add more filters as needed
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"filtered_{filter_type}.png")
            img.save(output_path, format='PNG')
        return output_path
    except Exception as e:
        logger.error(f"Error applying filter: {e}")
        return None

def create_homescreen_mockup(icon_path):
    """
    Overlay the icon onto a homescreen mockup image.
    """
    mockup_path = os.path.join('static', 'mockups', 'homescreen_mockup.png')
    if not os.path.exists(mockup_path):
        return None

    try:
        with Image.open(mockup_path) as bg:
            with Image.open(icon_path) as icon:
                # Position icon on mockup (for demonstration, place at a fixed position)
                icon = icon.resize((180, 180), Image.LANCZOS)  # typical icon size for mockup
                bg.paste(icon, (100, 300), icon)
                output_path = os.path.join(app.config['OUTPUT_FOLDER'], 'homescreen_preview.png')
                bg.save(output_path, format='PNG')
        return output_path
    except Exception as e:
        logger.error(f"Error creating homescreen mockup: {e}")
        return None

def overlay_frame(input_path):
    """
    Overlay the uploaded image onto an iPhone frame to create a marketing screenshot.
    """
    frame_path = os.path.join('static', 'frames', 'iphone_frame.png')
    if not os.path.exists(frame_path):
        return None

    try:
        with Image.open(frame_path) as frame:
            with Image.open(input_path) as img:
                # For demonstration, assume frame inner display size and position
                frame_width, frame_height = frame.size
                # Assume a known display area where the screenshot should be placed
                # This would be determined by the frame's design. Let's say it's 600x1300 at (200,300).
                display_x, display_y = 200, 300
                display_w, display_h = 600, 1300
                screenshot = img.resize((display_w, display_h), Image.LANCZOS)
                frame.paste(screenshot, (display_x, display_y))
                output_path = os.path.join(app.config['OUTPUT_FOLDER'], 'framed_screenshot.png')
                frame.save(output_path, 'PNG')
        return output_path
    except Exception as e:
        logger.error(f"Error overlaying frame: {e}")
        return None

def convert_color_profile(input_path):
    """
    Convert the image to sRGB color profile (simplified).
    In reality, you might need `ImageCms` and ICC profiles.
    """
    try:
        with Image.open(input_path) as img:
            # Just ensure mode is RGB
            img = img.convert('RGB')
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], 'srgb_converted.png')
            img.save(output_path, format='PNG')
        return output_path
    except Exception as e:
        logger.error(f"Error converting color profile: {e}")
        return None

def generate_launch_screen(input_path):
    """
    Create a launch screen image by placing input image over a background.
    """
    bg_path = os.path.join('static', 'backgrounds', 'launch_background.png')
    if not os.path.exists(bg_path):
        return None

    try:
        with Image.open(bg_path) as bg:
            with Image.open(input_path) as fg:
                bg_w, bg_h = bg.size
                # Resize fg to fit nicely in the center
                fg = fg.resize((int(bg_w*0.5), int(bg_h*0.5)), Image.LANCZOS)
                fg_w, fg_h = fg.size
                offset = ((bg_w - fg_w)//2, (bg_h - fg_h)//2)
                bg.paste(fg, offset, fg if fg.mode=='RGBA' else None)
                output_path = os.path.join(app.config['OUTPUT_FOLDER'], 'launch_screen.png')
                bg.save(output_path, 'PNG')
        return output_path
    except Exception as e:
        logger.error(f"Error generating launch screen: {e}")
        return None

def generate_typography_preview(text="Hello, iOS!", font_size=72):
    """
    Generate a sample text image using a system-like font (e.g., San Francisco).
    """
    font_path = os.path.join('static', 'fonts', 'SanFrancisco.ttf')
    if not os.path.exists(font_path):
        return None

    try:
        # Create a blank image and draw text
        img = Image.new('RGBA', (1200, 200), (255,255,255,0))
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(font_path, font_size)
        text_w, text_h = draw.textsize(text, font=font)
        draw.text(((1200-text_w)//2, (200-text_h)//2), text, font=font, fill=(0,0,0,255))
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], 'typography_preview.png')
        img.save(output_path, 'PNG')
        return output_path
    except Exception as e:
        logger.error(f"Error generating typography preview: {e}")
        return None

def zip_files(file_paths, zip_name='assets.zip'):
    zip_path = os.path.join(app.config['OUTPUT_FOLDER'], zip_name)
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for fp in file_paths:
            zf.write(fp, os.path.basename(fp))
    return zip_path

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/instructions')
def instructions():
    return render_template('instructions.html')

@app.route('/convert', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        # Check for file presence
        if 'file' not in request.files:
            flash("No file part found in the request.")
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash("No file selected. Please choose an image.")
            return redirect(request.url)

        if file:
            input_image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(input_image_path)

            output_image_path = os.path.join(app.config['OUTPUT_FOLDER'], 'converted_image.png')
            success = convert_image(input_image_path, output_image_path)

            if success:
                return redirect(url_for('preview_image', filename='converted_image.png'))
            else:
                flash("An error occurred during conversion. Please try again with a valid image.")
                return redirect(request.url)

    return render_template('upload_form.html')

@app.route('/preview/<filename>')
def preview_image(filename):
    output_image_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if not os.path.exists(output_image_path):
        flash("The requested file does not exist.")
        return redirect(url_for('upload_image'))
    return render_template('preview.html', filename=filename)

@app.route('/download/<filename>')
def download_image(filename):
    output_image_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if os.path.exists(output_image_path):
        return send_file(output_image_path, mimetype='image/png', as_attachment=True)
    else:
        flash("The requested file does not exist.")
        return redirect(url_for('upload_image'))

@app.route('/serve_pdfsage')
def serve_pdfsage():
    pdfsage_path = os.path.join('static', 'PDFSage.png')
    if os.path.exists(pdfsage_path):
        return send_file(pdfsage_path, mimetype='image/png')
    else:
        flash("PDFSage.png not found on the server.")
        return redirect(url_for('index'))

@app.route('/generate_icon_set', methods=['POST'])
def generate_icon_set():
    # Requires an uploaded file, which should be processed first
    if 'file' not in request.files:
        flash("No file uploaded for icon set generation.")
        return redirect(url_for('upload_image'))

    file = request.files['file']
    if file.filename == '':
        flash("No file selected for icon set generation.")
        return redirect(url_for('upload_image'))

    input_image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(input_image_path)
    icon_paths = generate_ios_app_icons(input_image_path)

    if not icon_paths:
        flash("Failed to generate icon set.")
        return redirect(url_for('upload_image'))

    # Zip the generated icons
    zip_path = zip_files(icon_paths, 'ios_app_icons.zip')
    return render_template('icon_set_generated.html', zip_path=os.path.basename(zip_path))

@app.route('/download_assets/<filename>')
def download_assets(filename):
    assets_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if os.path.exists(assets_path):
        return send_file(assets_path, as_attachment=True)
    else:
        flash("The requested asset file does not exist.")
        return redirect(url_for('index'))

@app.route('/filters', methods=['GET', 'POST'])
def filters():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file selected.")
            return redirect(request.url)
        file = request.files['file']
        filter_type = request.form.get('filter_type', 'grayscale')
        input_image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(input_image_path)
        filtered_path = apply_filter_to_image(input_image_path, filter_type)
        if filtered_path:
            return send_file(filtered_path, as_attachment=True)
        else:
            flash("Error applying filter.")
            return redirect(request.url)

    return render_template('filters.html')

@app.route('/homescreen_mockup/<filename>')
def homescreen_mockup(filename):
    output_image_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    mockup_path = create_homescreen_mockup(output_image_path)
    if mockup_path:
        return render_template('mockup_preview.html', mockup_filename=os.path.basename(mockup_path))
    else:
        flash("Error creating homescreen mockup.")
        return redirect(url_for('preview_image', filename=filename))

@app.route('/frame_screenshot', methods=['POST'])
def frame_screenshot():
    if 'file' not in request.files:
        flash("No file selected.")
        return redirect(url_for('upload_image'))
    file = request.files['file']
    input_image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(input_image_path)
    framed_path = overlay_frame(input_image_path)
    if framed_path:
        return render_template('frame_preview.html', frame_filename=os.path.basename(framed_path))
    else:
        flash("Error creating framed screenshot.")
        return redirect(url_for('upload_image'))

@app.route('/convert_color_profile', methods=['POST'])
def convert_profile():
    if 'file' not in request.files:
        flash("No file selected.")
        return redirect(url_for('upload_image'))
    file = request.files['file']
    input_image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(input_image_path)
    srgb_path = convert_color_profile(input_image_path)
    if srgb_path:
        return send_file(srgb_path, as_attachment=True)
    else:
        flash("Error converting color profile.")
        return redirect(url_for('upload_image'))

@app.route('/generate_launch_screen', methods=['POST'])
def create_launch_screen():
    if 'file' not in request.files:
        flash("No file selected.")
        return redirect(url_for('upload_image'))
    file = request.files['file']
    input_image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(input_image_path)
    launch_path = generate_launch_screen(input_image_path)
    if launch_path:
        return render_template('launch_screen_generated.html', launch_filename=os.path.basename(launch_path))
    else:
        flash("Error generating launch screen.")
        return redirect(url_for('upload_image'))

@app.route('/typography_preview', methods=['GET', 'POST'])
def typography_preview():
    if request.method == 'POST':
        text = request.form.get('text', 'Hello, iOS!')
        font_size = int(request.form.get('font_size', 72))
        preview_path = generate_typography_preview(text=text, font_size=font_size)
        if preview_path:
            return render_template('typography_preview.html', preview_filename=os.path.basename(preview_path))
        else:
            flash("Error generating typography preview.")
            return redirect(request.url)

    return render_template('typography_preview.html')

if __name__ == '__main__':
    # In production, use Gunicorn or another WSGI server:
    # gunicorn -w 4 -b 0.0.0.0:529 app:app
    app.run(host='0.0.0.0', port=599, debug=False)
