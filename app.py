from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Placeholder data structures (replace with database implementation)
tenants = []
maintenance_requests = []


# Route for the root URL
@app.route('/')
def home():
    return "Welcome to the Maintenance App!"


# Routes for Tenant
@app.route('/submit_request', methods=['GET', 'POST'])
def submit_request():
    if request.method == 'POST':
        # Handle form submission and request creation
        area = request.form['area']
        description = request.form['description']
        photo = request.files['photo'] if 'photo' in request.files else None

        # Placeholder logic to generate request ID and date/time
        request_id = len(maintenance_requests) + 1

        # Placeholder logic to get the current tenant (replace with authentication)
        tenant = tenants[0] if tenants else None

        # Placeholder logic to update the status of the request
        status = 'pending'

        maintenance_request = {
            'id': request_id,
            'apartment_number': tenant['apartment_number'],
            'area': area,
            'description': description,
            'date_time': '2023-12-03 12:00:00',  # Placeholder for current date/time
            'photo': photo,
            'status': status,
        }

        maintenance_requests.append(maintenance_request)

        return redirect(url_for('submit_request'))

    return render_template('submit_request.html')


# Routes for Staff Member
@app.route('/browse_requests', methods=['GET'])
def browse_requests():
    # Display maintenance requests with filters
    filters = request.args.to_dict()

    filtered_requests = maintenance_requests
    for key, value in filters.items():
        if key in ['apartment_number', 'area', 'date_time', 'status']:
            filtered_requests = [req for req in filtered_requests if req.get(key) == value]

    return render_template('browse_requests.html', maintenance_requests=filtered_requests)


@app.route('/update_status/<int:request_id>', methods=['POST'])
def update_status(request_id):
    # Update status of the selected request
    for request_obj in maintenance_requests:
        if request_obj['id'] == request_id:
            request_obj['status'] = 'completed'
            break

    return redirect(url_for('browse_requests'))


# Routes for Manager
@app.route('/add_tenant', methods=['GET', 'POST'])
def add_tenant():
    if request.method == 'POST':
        # Handle form submission and add a new tenant
        tenant_id = len(tenants) + 1
        name = request.form['name']
        phone_number = request.form['phone_number']
        email = request.form['email']
        check_in_date = request.form['check_in_date']
        check_out_date = request.form['check_out_date']
        apartment_number = request.form['apartment_number']

        tenant = {
            'id': tenant_id,
            'name': name,
            'phone_number': phone_number,
            'email': email,
            'check_in_date': check_in_date,
            'check_out_date': check_out_date,
            'apartment_number': apartment_number,
        }

        tenants.append(tenant)

        return redirect(url_for('add_tenant'))

    return render_template('add_tenant.html')


@app.route('/move_tenant/<int:tenant_id>', methods=['POST'])
def move_tenant(tenant_id):
    # Move a tenant to another apartment
    # Placeholder logic, update the apartment number of the selected tenant
    for tenant in tenants:
        if tenant['id'] == tenant_id:
            tenant['apartment_number'] = request.form['new_apartment_number']
            break

    return redirect(url_for('browse_tenants'))


@app.route('/delete_tenant/<int:tenant_id>', methods=['POST'])
def delete_tenant(tenant_id):
    # Delete a tenant
    global tenants
    tenants = [tenant for tenant in tenants if tenant['id'] != tenant_id]

    return redirect(url_for('browse_tenants'))


# Route to display all tenants (for manager)
@app.route('/browse_tenants')
def browse_tenants():
    return render_template('browse_tenants.html', tenants=tenants)


if __name__ == '__main__':
    app.run(debug=True)
