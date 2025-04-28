from flask import Blueprint, render_template

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def index():
    return render_template('index.html')

@public_bp.route('/about')
def about():
    return render_template('about.html')

@public_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Placeholder: process form data here
        return jsonify({'message': 'Contact form submitted successfully'})
    return render_template('contact.html')
