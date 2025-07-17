import os
from jetson_inference import imageNet
from jetson_utils import loadImage, saveImage, cudaFont
from flask import Flask, request, render_template, after_this_request

app = Flask(__name__)
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

for filename in os.listdir(UPLOAD_FOLDER):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.isfile(file_path):
        os.remove(file_path)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload():
    result = None
    img_filename = None

    if request.method == 'POST':
        if 'file' not in request.files:
            result = "No file part"
            return render_template('upload.html', result=result, img_filename=None)
        file = request.files['file']
        if file.filename == '':
            result = "No selected file"
            return render_template('upload.html', result=result, img_filename=None)
        if file and allowed_file(file.filename):
            img_filename = os.path.join(UPLOAD_FOLDER, file.filename)
            annotated_img_filename = os.path.join(UPLOAD_FOLDER, 'annotated_' + file.filename)
            file.save(img_filename)

            input_image = loadImage(img_filename)

            net = imageNet(model="/home/nvidia/final/spacemodel/resnet18.onnx", labels="/home/nvidia/final/spacemodel/labels.txt",
                           input_blob="input_0", output_blob="output_0")

            class_idx, confidence = net.Classify(input_image)
            class_desc = net.GetClassDesc(class_idx)

            overlay_text = "{:s} ({:.2f}%)".format(class_desc, confidence * 100)
            font = cudaFont()
            font.OverlayText(input_image, 0, 0, overlay_text, 0, 0, font.White, font.Gray40)

            saveImage(annotated_img_filename, input_image)

            result = "Image recognized as '{}' (class #{}) with {:.2f}% confidence".format(
                class_desc, class_idx, confidence * 100)

            return render_template('result.html', result=result, img_filename='images/annotated_' + file.filename)

        else:
            result = "File type not allowed"
            return render_template('upload.html', result=result, img_filename=None)

    return render_template('upload.html', result=None, img_filename=None)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
