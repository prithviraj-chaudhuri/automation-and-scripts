from flask import Flask, request, jsonify
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload-image', methods=['POST'])
def upload_image():
    print("Received request to upload image")
    print("Request data:", )
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    image = request.files['image']

    if image.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    file_path = os.path.join(UPLOAD_FOLDER, image.filename)
    image.save(file_path)

    return jsonify({'message': 'Image uploaded successfully', 'file_path': file_path}), 200


@app.route('/test', methods=['GET'])
def test():
    """
    Simple endpoint to test if the service is running.
    Returns a JSON response with a success message.
    """
    return jsonify({
        'status': 'success',
        'message': 'The upload service is running correctly'
    }), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port="5001", debug=True)