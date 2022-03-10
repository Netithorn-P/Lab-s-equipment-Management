from flask import Flask , render_template, redirect, url_for, request
from flask_login.utils import login_required 
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, TextAreaField
from wtforms.fields.core import SelectField
from wtforms.validators import  InputRequired, Length, Email
from flask_login import LoginManager, UserMixin, login_manager, login_user, logout_user, current_user
import serverDB

conn = f'mysql+pymysql://{serverDB.db_user}:{serverDB.db_password}@{serverDB.db_host}:{serverDB.db_port}/{serverDB.db_name}'
# conn = 'sqlite:///database.db'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'DREAM_LabsProjectDB'
app.config['SQLALCHEMY_DATABASE_URI'] = conn
db = SQLAlchemy(app)
ma = Marshmallow(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

Bootstrap(app)

# database model structure

class equipment_database(db.Model):
    __table_args__ = { 	'mysql_engine': 'InnoDB',  	'mysql_charset': 'utf8', 	'mysql_collate': 'utf8_general_ci' }
    id = db.Column(db.Integer,primary_key=True) #Ex. '1','2'
    device = db.Column(db.String(50), unique=True, nullable=False) #Ex. 'DEREE DE-208E','POWERS0001'
    type = db.Column(db.String(50), nullable=False)  #Ex. 'Multimeter','PowerSupply'
    serial = db.Column(db.String(50), unique=True, nullable=False) #Ex. 'N00016141','PS000001'
    status = db.Column(db.String(50), db.ForeignKey('user_database.name')) #Ex. 'Available' or 'user.name' *In use*
    description = db.Column(db.String(255)) 
    device_user = db.relationship('user_database', backref='usingdevice')
 
    def __repr__(self):
        return f'id: {self.id} | device: {self.device} | serial: {self.serial} | status: {self.status} | description: {self.description} |' 

class user_database(UserMixin, db.Model): 
    __table_args__ = { 	'mysql_engine': 'InnoDB',  	'mysql_charset': 'utf8', 	'mysql_collate': 'utf8_general_ci' }
    id = db.Column(db.Integer , primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False) #Ex. 'Netithorn Preechapattananont','Available','Unavailable'
    email = db.Column(db.String(50), unique=True, nullable=False) #Ex. 'pr.netithorn_st@tni.ac.th','a.dream_lab@tni.ac.th','u.dream_lab@tni.ac.th'
    tni_id = db.Column(db.String(10), unique=True, nullable=False) #Ex. '60115041-0','111111','000000'
    type = db.Column(db.String(50), nullable=False) #Ex. 'Student','Other','Other'
    description = db.Column(db.String(255)) #Ex. '','Available status','Unavailable status'

@login_manager.user_loader
def load_user(user_id):
    return user_database.query.get(int(user_id))    

# db.create_all()


# form class

class loginForm(FlaskForm):
     email = StringField('E-mail', validators=[InputRequired(), Email(message='Please Enter your TNI E-mail'), Length(min=5, max=40)])
     tni_id = StringField('TNI ID', validators=[InputRequired(), Length(min=6, max=80)])
     remember = BooleanField('Remember Me')

class registerForm(FlaskForm):
     email = StringField('E-mail', validators=[InputRequired(message="Plesa enter your E-mail"), Email(message='Please Enter your TNI E-mail'), Length(min=5, max=40)])
     tni_id = StringField('TNI ID', validators=[InputRequired(message="Plesa enter your TNI ID"), Length(min=6, max=80)])
     name = StringField('Name', validators=[InputRequired(message="Plesa enter your name"),])
     type = SelectField('Member position', choices=[('Student','Student'),('Teacher','Teacher'),('Other','Other')], validators=[InputRequired(message='Please choose your position')])
     description = TextAreaField('Description')

class EquipmentForm(FlaskForm):
     device = StringField('Device', validators=[InputRequired()])
     type = SelectField('Device Type',choices=[('Multimeter','Multimeter'),('Power Supply','Power Supply'),('Oscilloscope','Oscilloscope'),('Signal generator','Signal generator'),('MCU','MCU'),('Sensor','Sensor'),('Other','Other')], validators=[InputRequired(message='Please choose device type')])
     serial = StringField('Serial', validators=[InputRequired()])
     status = SelectField('Status',choices=[('Available','Available'),('Unavailable','Unavailable')], validators=[InputRequired(message='Please choose status')])
     description = TextAreaField('Description')


#Site Route

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login',methods=['GET','POST'])
def login():
    form = loginForm()
    
    if form.validate_on_submit():
        email = user_database.query.filter_by(email=form.email.data).first()
        if email:
            if email.tni_id == form.tni_id.data:
                login_user(email, remember=form.remember.data)
                return redirect(url_for('dashboard'))
        
        return '<h1> Invalid email or tni_id </h1>' 

    return render_template('login.html', form=form) 


@app.route('/signup', methods=['GET','POST'])
def signup():
    form = registerForm()

    if form.validate_on_submit():
        # hashed_password = generate_password_hash(form.password.data, method='sha256')
        # new_user = user_database(name=form.name.data,  email=form.email.data, password=hashed_password, type=form.type.data)
        new_user = user_database(name=form.name.data,  email=form.email.data, tni_id=form.tni_id.data, type=form.type.data)
        db.session.add(new_user)
        db.session.commit()
        # return '<h1> New user has been create </h1>'
        return redirect(url_for('login'))

    return render_template('signup.html', form=form)


@app.route('/dashboard', methods=['GET','POST'])
@login_required
def dashboard():

    user_name = current_user.name
    admin_check = user_database.query.filter_by(name=user_name).first().description
    data = equipment_database.query.all() 
    filter = request.args.get('radio')
        
    if filter == 'All Devices' :
        data = equipment_database.query.all()
    elif filter == 'My Workbench':
        data = equipment_database.query.filter_by(status=user_name).all()
    else:
        data = equipment_database.query.filter_by(type=filter).all()

        
    if request.method == 'POST':     
      
        action = request.form.get('subbt') 
        deviceid = request.form.get('deviceid')         
        data = equipment_database.query.filter_by(status=user_name).all() 
        filter = request.form.get('filter')       

        if filter == 'All' :
            data = equipment_database.query.all()
        elif filter == 'My':
            data = equipment_database.query.filter_by(status=user_name).all()
        elif filter == 'Other':
            data = equipment_database.query.filter_by(type='Other').all()
        elif filter == 'Signal':
            data = equipment_database.query.filter_by(type='Signal generator').all()
        else:
            data = equipment_database.query.filter_by(type=filter).all()
        
        if action == 'Pick':
            device_update = equipment_database.query.filter_by(id=deviceid).first()
            device_update.status = current_user.name
            db.session.commit()   
        elif action == 'Return':
            device_update = equipment_database.query.filter_by(id=deviceid).first()
            device_update.status = 'Available'
            db.session.commit()  
                                     
    return render_template('dashboard.html',name = current_user.name, data = data, filter = filter, permission = admin_check )


@app.route('/dashboard/ad_manage', methods=['GET','POST'])
@login_required
def admin_manage():

    form = EquipmentForm()

    user_name = current_user.name
    admin_check = user_database.query.filter_by(name=user_name).first().description
    data = equipment_database.query.all()
    filter = request.args.get('radio')
         
    if filter == 'All Devices' :
        data = equipment_database.query.all()
    else:
        data = equipment_database.query.filter_by(type=filter).all()

        
    if request.method == 'POST':     
      
        action = request.form.get('subbt') 
        deviceid = request.form.get('deviceid')         
        filter = request.form.get('filter')
    
        if filter == 'All' :
            data = equipment_database.query.all()
        elif filter == 'Other':
            data = equipment_database.query.filter_by(type='Other').all()
        elif filter == 'Signal':
            data = equipment_database.query.filter_by(type='Signal generator').all()
        else:
            data = equipment_database.query.filter_by(type=filter).all()
        
        if action == 'Edit':
            device_edit = equipment_database.query.filter_by(id=deviceid).first()
            device_edit.device = request.form.get('device') 
            device_edit.type = request.form.get('type') 
            device_edit.serial = request.form.get('serial') 
            device_edit.status = request.form.get('status') 
            device_edit.description = request.form.get('description') 
            db.session.commit()            
            pass       
        elif action == 'Add':
            new_device = equipment_database(device=form.device.data ,  type=form.type.data, serial=form.serial.data, status=form.status.data, description = form.description.data)
            db.session.add(new_device)
            db.session.commit() 
            pass
        elif action == 'Remove':
            device_delete = equipment_database.query.filter_by(id=deviceid).first()
            db.session.delete(device_delete)
            db.session.commit()            
            return redirect(url_for('admin_manage'))
                                      
    return render_template('admin_devicemanage.html',name = current_user.name, data = data, filter = filter, permission = admin_check , form = form)
       

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)
