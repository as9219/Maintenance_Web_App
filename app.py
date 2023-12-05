import random
import string
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import db
from flask import Flask, render_template, request, redirect, url_for
from flask import session, abort
from datetime import datetime

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

cred = credentials.Certificate("maintenancewebapp-key.json")
firebase_admin.initialize_app(cred, {"databaseURL": "https://maintenancewebapp-default-rtdb.firebaseio.com/"})

db = firestore.client()


def generate_password(length=8):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))


# root homepage
@app.route('/')
def home():
    return render_template('login.html')


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
                    print("Email : Role ", role, " ; ", email)  # remove

                    if role == "admin":
                        return redirect(url_for('admin_dashboard'))
                    elif role == "management":
                        return redirect(url_for('management_dashboard'))
                    elif role == "staff":
                        return redirect(url_for('staff_dashboard'))
                    else:
                        return redirect(url_for('tenant_dashboard'))

    return redirect(url_for('home'))


@app.route('/admin/dashboard')
def admin_dashboard():
    if 'email' in session and session.get('role') == 'admin':
        return render_template('admin_dashboard.html')
    else:
        abort(403) # not authorized error


@app.route('/management/dashboard')
def management_dashboard():
    if 'email' in session and session.get('role') == 'management':
        return render_template('management_dashboard.html')
    else:
        abort(403)


@app.route('/staff/dashboard')
def staff_dashboard():
    if 'email' in session and session.get('role') == 'staff':
        return render_template('staff_dashboard.html')
    else:
        abort(403)


@app.route('/tenant/dashboard')
def tenant_dashboard():
    if 'email' in session and session.get('role') == 'tenant':
        return render_template('tenant_dashboard.html')
    else:
        abort(403)


# incomplete function
@app.route('/submit_request', methods=['GET', 'POST'])
def submit_request():
    if request.method == 'POST':
        area = request.form['area']
        description = request.form['description']
        photo = request.files['photo'] if 'photo' in request.files else None

        # request_id = db.collection('maintenance_requests').document().id
        # tenant = db.collection('tenants').limit(1).get()[0].to_dict() if db.collection('tenants').limit(1).get() else None
        status = 'pending'

        maintenance_request = {
            # 'id': request_id,
            # 'apartment_number': tenant['apartment_number'],
            'area': area,
            'description': description,
            'date_time': '2023-12-03 12:00:00',  # Placeholder for current date/time
            'photo': photo,
            'status': status,
        }

        # db.collection('maintenance_requests').add(maintenance_request)

        return redirect(url_for('submit_request'))

    return render_template('submit_request.html')


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
            'apartment_number': apartment_number,
        }

        db.document(f'tenants/{tenant_email}').set(tenant_data)

        login_data = {
            'email': tenant_email,
            'password': tenant_password,
        }
        db.document(f'loginID/{tenant_email}').set(login_data)

        return redirect(url_for('add_tenant'))

    return render_template('add_tenant.html')


# incomplete function
@app.route('/browse_requests', methods=['GET'])
def browse_requests():
    filters = request.args.to_dict()
    maintenance_requests = []

    # maintenance_requests_ref = db.collection('maintenance_requests')

    for key, value in filters.items():
        if key in ['apartment_number', 'area', 'date_time', 'status']:
            maintenance_requests_ref = maintenance_requests_ref.where(key, '==', value)

    # docs = maintenance_requests_ref.stream()

    # for doc in docs:
    #    maintenance_requests.append(doc.to_dict())

    # return render_template('browse_requests.html', maintenance_requests=maintenance_requests)


@app.route('/browse_tenants')
def browse_tenants():
    tenants = []
    tenants_ref = db.collection('tenants').stream()

    for tenant_doc in tenants_ref:
        tenants.append(tenant_doc.to_dict())

    return render_template('browse_tenants.html', tenants=tenants)


if __name__ == '__main__':
    app.run(debug=True)
