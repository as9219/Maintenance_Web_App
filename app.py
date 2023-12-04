import uuid
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import db
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Initialize Firebase with your credentials
cred = credentials.Certificate("maintenancewebapp-key.json")
firebase_admin.initialize_app(cred, {"databaseURL": "https://maintenancewebapp-default-rtdb.firebaseio.com/"})

# Get a reference to the Firestore database
db = firestore.client()


@app.route('/')
def home():
    return "Welcome to the Maintenance App!"


# Routes for Tenant
@app.route('/submit_request', methods=['POST'])
def submit_request():
    if request.method == 'POST':
        area = request.form['area']
        description = request.form['description']
        photo = request.files['photo'] if 'photo' in request.files else None

        # Generate request ID and date/time
        #request_id = db.collection('maintenance_requests').document().id
        #tenant = db.collection('tenants').limit(1).get()[0].to_dict() if db.collection('tenants').limit(1).get() else None
        status = 'pending'

        maintenance_request = {
            #'id': request_id,
            #'apartment_number': tenant['apartment_number'],
            'area': area,
            'description': description,
            'date_time': '2023-12-03 12:00:00',  # Placeholder for current date/time
            'photo': photo,
            'status': status,
        }

        # Add maintenance request to Firestore
        #db.collection('maintenance_requests').add(maintenance_request)

        return redirect(url_for('submit_request'))

    return render_template('submit_request.html')

# Routes for Manager
@app.route('/add_tenant', methods=['GET', 'POST'])
def add_tenant():
    if request.method == 'POST':
        # Generate a unique ID for the new tenant
        tenant_id = str(uuid.uuid4())  # Use UUID as a unique identifier

        name = request.form['name']
        phone_number = request.form['phone_number']
        email = request.form['email']
        check_in_date = request.form['check_in_date']
        check_out_date = request.form['check_out_date']
        apartment_number = request.form['apartment_number']

        tenant_data = {
            'id': tenant_id,
            'name': name,
            'phone_number': phone_number,
            'email': email,
            'check_in_date': check_in_date,
            'check_out_date': check_out_date,
            'apartment_number': apartment_number,
        }

        # Add the tenant data to Firestore
        db.document(f'tenants/{tenant_id}').set(tenant_data)

        return redirect(url_for('add_tenant'))

    return render_template('add_tenant.html')

# Routes for Staff Member
@app.route('/browse_requests', methods=['GET'])
def browse_requests():
    filters = request.args.to_dict()
    maintenance_requests = []

    # Fetch maintenance requests from Firestore based on filters
    #maintenance_requests_ref = db.collection('maintenance_requests')

    for key, value in filters.items():
        if key in ['apartment_number', 'area', 'date_time', 'status']:
            maintenance_requests_ref = maintenance_requests_ref.where(key, '==', value)

    #docs = maintenance_requests_ref.stream()

    #for doc in docs:
    #    maintenance_requests.append(doc.to_dict())

    #return render_template('browse_requests.html', maintenance_requests=maintenance_requests)

# Route to display all tenants (for manager)
@app.route('/browse_tenants')
def browse_tenants():
    tenants = []
    tenants_ref = db.collection('tenants').stream()

    for tenant_doc in tenants_ref:
        tenants.append(tenant_doc.to_dict())

    return render_template('browse_tenants.html', tenants=tenants)

if __name__ == '__main__':
    app.run(debug=True)
