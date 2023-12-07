import random
import string
import firebase_admin
from firebase_admin import credentials, firestore, storage
from firebase_admin import db
from flask import Flask, render_template, request, redirect, url_for
from flask import session, abort
from datetime import datetime

cred = credentials.Certificate("maintenancewebapp-key.json")
firebase_admin.initialize_app(cred, {"databaseURL": "https://maintenancewebapp-default-rtdb.firebaseio.com/"})
storage_app = firebase_admin.initialize_app(cred, {'storageBucket': 'maintenancewebapp.appspot.com'}, name='storage')

db = firestore.client()
bucket = storage.bucket(app=storage_app)

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


# generates password for new tenant
def generate_password(length=8):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))


# root homepage
@app.route('/')
def home():
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()

    return redirect(url_for('home'))

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        login_doc = db.document(f'loginID/{email}').get()
        if login_doc.exists:
            login_data = login_doc.to_dict()
            if login_data['password'] == password:
                # check user's role from the 'tenants' collection
                tenant_doc = db.document(f'loginID/{email}').get()
                if tenant_doc.exists:
                    tenant_data = tenant_doc.to_dict()
                    role = tenant_data.get('role', 'tenant')  # default role is 'tenant' if not specified

                    session['email'] = email
                    session['role'] = role

                    if role == "admin":
                        return redirect(url_for('admin_dashboard'))
                    elif role == "management":
                        return redirect(url_for('management_dashboard'))
                    elif role == "staff":
                        return redirect(url_for('staff_dashboard'))
                    else:
                        return redirect(url_for('tenant_dashboard'))

    return redirect(url_for('home'))


@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'email' in session and session.get('role') == 'admin':
        return render_template('admin_dashboard.html')
    else:
        abort(403)  # not authorized error


@app.route('/management/dashboard', methods=['GET', 'POST'])
def management_dashboard():
    if 'email' in session and session.get('role') == 'management':
        return render_template('management_dashboard.html')
    else:
        abort(403)


@app.route('/staff/dashboard', methods=['GET', 'POST'])
def staff_dashboard():
    if 'email' in session and session.get('role') == 'staff':
        return render_template('staff_dashboard.html')
    else:
        abort(403)


@app.route('/tenant/dashboard', methods=['GET', 'POST'])
def tenant_dashboard():
    if 'email' in session and session.get('role') == 'tenant':
        return render_template('tenant_dashboard.html')
    else:
        abort(403)


UPLOAD_FOLDER = 'imageUploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/submit_request', methods=['GET', 'POST'])
def submit_request():
    if request.method == 'POST':
        area = request.form['area']
        description = request.form['description']
        photo = request.files['photo'] if 'photo' in request.files else None

        # unique id using db import
        request_id = db.collection('maintenanceRequests').document().id

        tenant_email = session.get('email')
        tenant_doc = db.collection('tenants').document(tenant_email).get()

        if tenant_doc.exists:
            tenant = tenant_doc.to_dict()

            # grab current sys time
            sys_time = datetime.now()
            formatted_time = sys_time.strftime("%b/%d/%Y - %H:%M:%S")

            status = 'Pending'
            maintenance_request = {
                'id': request_id,
                'apartment_number': tenant['apartment_number'],
                'area': area,
                'description': description,
                'date_time': formatted_time,
                'status': status,
                'photo': None
            }

            if photo:
                photo_filename = f"{maintenance_request['id']}_{photo.filename}"
                # photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
                # photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
                # Save the file path in the database
                blob = bucket.blob(photo_filename)
                blob.upload_from_file(photo, content_type=photo.content_type)
                maintenance_request["photo"] = blob.public_url

            db.document(f'maintenanceRequests/{request_id}').set(maintenance_request)

            return redirect(url_for('tenant_dashboard'))

    return render_template('submit_request.html')


@app.route('/complete_request/<request_id>', methods=['GET', 'POST'])
def complete_request(request_id):
    # Assuming you want to set the status to "Complete" in the document
    db.document(f'maintenanceRequests/{request_id}').update({"status": "Complete"})

    return redirect(url_for('browse_requests'))


@app.route('/add_tenant', methods=['GET', 'POST'])
def add_tenant():
    if request.method == 'POST':
        tenant_email = request.form['email']

        name = request.form['name']
        phone_number = request.form['phone_number']
        check_in_date = request.form['check_in_date']
        check_out_date = request.form['check_out_date']
        apartment_number = request.form['apartment_number']

        tenant_password = generate_password()

        tenant_data = {
            'id': tenant_email,
            'name': name,
            'phone_number': phone_number,
            'check_in_date': check_in_date,
            'check_out_date': check_out_date,
            'apartment_number': apartment_number
        }

        db.document(f'tenants/{tenant_email}').set(tenant_data)

        login_data = {
            'email': tenant_email,
            'password': tenant_password,
            'role': 'tenant'
        }
        db.document(f'loginID/{tenant_email}').set(login_data)

        return redirect(url_for('management_dashboard'))

    return render_template('add_tenant.html')


@app.route('/move_tenant/<tenant_id>', methods=['GET', 'POST'])
def move_tenant(tenant_id):
    if request.method == 'POST':
        new_apartment_number = request.form['new_apartment_number']
        # Update the tenant's apartment number in the database
        db.document(f'tenants/{tenant_id}').update({'apartment_number': new_apartment_number})
        return redirect(url_for('browse_tenants', role='management'))

    return render_template('move_tenant.html', tenant_id=tenant_id)


@app.route('/remove_tenant/<tenant_id>', methods=['GET', 'POST'])
def remove_tenant(tenant_id):
    tenant_doc = db.document(f'tenants/{tenant_id}').get()

    if tenant_doc.exists:
        db.document(f'tenants/{tenant_id}').delete()
        db.document(f'loginID/{tenant_id}').delete()

        return redirect(url_for('browse_tenants'))

    return render_template('management_dashboard.html')


@app.route('/browse_requests', methods=['GET'])
def browse_requests():
    maintenance_requests = []

    maintenance_requests_ref = db.collection('maintenanceRequests').stream()

    for maintenance_doc in maintenance_requests_ref:
        maintenance_requests.append(maintenance_doc.to_dict())

    return render_template('browse_requests.html', maintenance_requests=maintenance_requests)


@app.route('/search_requests', methods=['POST'])
def search_requests():
    search_criteria = request.form.get('search')
    if search_criteria:
        maintenance_requests_ref = db.collection('maintenanceRequests')
        unique_results = set()

        query_apartment = maintenance_requests_ref.where('apartment_number', '>=', search_criteria).stream()
        query_area = maintenance_requests_ref.where('area', '==', search_criteria).stream()
        query_status = maintenance_requests_ref.where('status', '==', search_criteria).stream()
        query_id = maintenance_requests_ref.where('id', '==', search_criteria).stream()

        unique_results.update(query_apartment)
        unique_results.update(query_area)
        unique_results.update(query_status)
        unique_results.update(query_id)

        maintenance_requests = [maintenance_doc.to_dict() for maintenance_doc in unique_results]

    else:
        maintenance_requests_ref = db.collection('maintenanceRequests').stream()
        maintenance_requests = [maintenance_doc.to_dict() for maintenance_doc in maintenance_requests_ref]

    return render_template('browse_requests.html', maintenance_requests=maintenance_requests)


@app.route('/browse_tenants')
def browse_tenants():
    tenants = []
    tenants_ref = db.collection('tenants').stream()

    for tenant_doc in tenants_ref:
        tenants.append(tenant_doc.to_dict())
    return render_template('browse_tenants.html', tenants=tenants)


if __name__ == '__main__':
    app.run(debug=True)
