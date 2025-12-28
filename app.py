import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import UserModel, TravelModel
from datetime import date

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = UserModel.authenticate(request.form['username'], request.form['password'])
        if user:
            session.update({
                'loggedin': True, 
                'username': user['username'], 
                'role': user['role']
            })
            flash(f'Selamat datang kembali, {user["username"]}!', 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))
        else:
            flash('Username atau Password salah!', 'danger')
            
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']

        if password != confirm_password:
            flash('Konfirmasi password tidak cocok!', 'danger')
        else:
            success, message = UserModel.register_user(username, password, role)
            if success:
                flash('Registrasi berhasil! Silakan login.', 'success')
                return redirect(url_for('login'))
            else:
                flash(message, 'danger')
    return render_template('auth/register.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    user = UserModel.get_user_profile(session['username'])
    
    if request.method == 'POST':
        new_pw = request.form.get('new_password')
        confirm_pw = request.form.get('confirm_password')
        
        if new_pw != confirm_pw:
            flash('Password tidak cocok!', 'danger')
        else:
            UserModel.update_password(session['username'], new_pw)
            flash('Password berhasil diganti!', 'success')
            
    return render_template('auth/profile.html', user=user)

# --- ADMIN ROUTES ---
@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin': 
        flash('Akses ditolak! Anda bukan admin.', 'danger')
        return redirect(url_for('login'))
    paket = TravelModel.get_all_packages()
    return render_template('admin/dashboard_admin.html', paket=paket)

@app.route('/admin/tambah', methods=['GET', 'POST'])
def tambah_paket():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    
    if request.method == 'POST':
        TravelModel.add_package(request.form['nama'], request.form['tujuan'], request.form['harga'])
        flash('Paket travel baru berhasil ditambahkan!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/tambah_paket.html')

@app.route('/admin/edit/<int:id>', methods=['GET', 'POST'])
def edit_paket(id):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    
    if request.method == 'POST':
        TravelModel.update_package(id, request.form['nama'], request.form['tujuan'], request.form['harga'])
        flash('Perubahan paket berhasil disimpan!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    paket = TravelModel.get_package_by_id(id)
    return render_template('admin/edit_paket.html', paket=paket)

@app.route('/admin/hapus/<int:id>')
def hapus_paket(id):
    if session.get('role') == 'admin':
        TravelModel.delete_package(id)
        flash('Paket travel telah dihapus.', 'warning')
    else:
        flash('Tindakan tidak diizinkan!', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/laporan')
def laporan_pesanan():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    laporan = TravelModel.get_semua_pesanan_admin()
    return render_template('admin/laporan_admin.html', laporan=laporan)

@app.route('/admin/pesanan/update/<int:id>/<string:status>')
def update_status(id, status):
    if session.get('role') != 'admin': 
        return redirect(url_for('login'))
    
    success, message = TravelModel.update_status_admin(id, status)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
        
    return redirect(url_for('laporan_pesanan'))

# --- USER ROUTES ---
@app.route('/user')
def user_dashboard():
    if 'loggedin' not in session: 
        flash('Silakan login untuk mengakses dashboard.', 'info')
        return redirect(url_for('login'))
    paket = TravelModel.get_all_packages()
    return render_template('user/dashboard_user.html', paket=paket)


@app.route('/user/pesan/form/<int:id>')
def form_pesan(id):
    if 'loggedin' not in session: return redirect(url_for('login'))
    paket = TravelModel.get_package_by_id(id)
    return render_template('user/form_pesan.html', paket=paket, current_date=date.today())

@app.route('/user/pesan/submit', methods=['POST'])
def submit_pesan():
    if 'loggedin' not in session: return redirect(url_for('login'))
    
    id_paket = request.form['id_paket']
    tgl_wisata = request.form['tgl_wisata'] 
    jumlah_orang = request.form['jumlah_orang']
    catatan = request.form['catatan']
    
    success = TravelModel.pesan_paket(session['username'], id_paket, tgl_wisata, jumlah_orang, catatan)
    
    if success:
        flash('Pesanan berhasil dibuat untuk tanggal ' + tgl_wisata, 'success')
        return redirect(url_for('pesanan_saya'))
    return redirect(url_for('user_dashboard'))

@app.route('/user/pesanan_saya')
def pesanan_saya():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    riwayat = TravelModel.get_pesanan_user(session['username'])
    return render_template('user/pesanan_user.html', pesanan=riwayat)

@app.route('/user/pesanan/batal/<int:id>')
def batal_pesanan(id):
    if 'loggedin' not in session: return redirect(url_for('login'))
    
    success, message = TravelModel.batal_pesanan_user(id, session['username'])
    
    category = 'warning' if success else 'danger'
    flash(message, category)
        
    return redirect(url_for('user_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah berhasil keluar.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)