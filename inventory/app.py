from flask import Flask, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from validate import validateLocation, validatProduct


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
db = SQLAlchemy(app)

class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    quantity = db.Column(db.Integer)

    def __str__(self):
        return "{}".format(self.name)
class Locations(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __str__(self):
        return "{}".format(self.name)

class ProductMovement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_location_id = db.Column(db.Integer(), db.ForeignKey(Locations.id))
    to_location_id = db.Column(db.Integer(), db.ForeignKey(Locations.id))
    product_id = db.Column(db.Integer(), db.ForeignKey(Products.id), nullable=False)
    from_location = db.relationship(Locations, foreign_keys=[from_location_id])
    to_location = db.relationship(Locations, foreign_keys=[to_location_id])
    product = db.relationship(Products, foreign_keys=[product_id])
    quantity = db.Column(db.Integer(), nullable=False)
    time_created = db.Column(db.DateTime, server_default=db.func.now())

    def __str__(self):
        return "{}".format(self.id)


@app.route('/')
def index():
    return render_template('index.html', mp = ProductMovement.query.all(), p = Products.query.all(), l = Locations.query.all())

@app.route('/products')
def products_view():
    return render_template('products.html', products = Products.query.all())

@app.route('/locations')
def locations_view():
    return render_template('locations.html', locations = Locations.query.all() )
@app.route('/moveproduct')
def move_view():
    return render_template('moveproduct.html', locations = Locations.query.all() , products = Products.query.all(), prmn = ProductMovement.query.all())

@app.route('/add_prod', methods = ['POST'])
def addProduct():
    if request.method == 'POST':
        product_name = request.form['name']
        product_quantity = request.form['quantity']
        if(validatProduct(product_name, product_quantity)):
            pc = Products.query.filter_by(name = product_name).first()
            if pc is not None:
                pc.quantity = int(product_quantity)
                db.session.commit()
                return render_template('products.html', products = Products.query.all())
            else:
                p = Products(name = product_name, quantity = product_quantity)
                db.session.add(p)
                db.session.commit()
                return render_template('products.html', products = Products.query.all())
        return render_template('products.html', products = Products.query.all(), message = "Enter the values")
    return render_template('products.html', products = Products.query.all(), message = "Something Wrong Pleas try again")
    

@app.route('/del_pro', methods = ['GET','POST'])
def deleteProduct():
    pr_id = request.args.get('prod_id')
    Products.query.filter_by(id=pr_id).delete()
    db.session.commit()
    return render_template('products.html', products = Products.query.all())

@app.route('/add_loc' , methods = ['POST'])
def addLocation():
    if request.method == 'POST':
        if(validateLocation(request.form['name'])):
            name = request.form['name']
            l = Locations(name = name)
            db.session.add(l)
            db.session.commit()
            return render_template('locations.html', locations = Locations.query.all() )
        return render_template('locations.html', locations = Locations.query.all() , message = "Enter location")
    return render_template('locations.html', locations = Locations.query.all(), message = "Something Wrong Pleas try again")

@app.route('/del_loc', methods = ['GET','POST'])
def deleteLocation():
    lc_id = request.args.get('loc_id')
    Locations.query.filter_by(id=lc_id).delete()
    db.session.commit()
    return render_template('locations.html', locations = Locations.query.all() )

@app.route('/new_move', methods = ['POST'])
def newMove():
    if request.method == 'POST':
        from_id = request.form['from']
        to_id = request.form['to']
        pr_id = request.form['product']
        qnty = request.form['quantity']
        if qnty == "":
            return render_template('moveproduct.html', locations = Locations.query.all() , products = Products.query.all(),prmn = ProductMovement.query.all(), message = "Quantity cant be Null")
        qty = int(qnty)
        
        if (from_id == to_id):
            return render_template('moveproduct.html', locations = Locations.query.all() , products = Products.query.all(),prmn = ProductMovement.query.all(), message = "Same Location not allowed")
        
        if (from_id == "" and to_id == ""):
            return render_template('moveproduct.html', locations = Locations.query.all() , products = Products.query.all(),prmn = ProductMovement.query.all(), message = "Please select Location")

        if from_id == "":
            p = Products.query.filter_by(id = pr_id).first()
            
            if p.quantity >= qty:
                p.quantity = p.quantity - qty
                db.session.commit()
                pm = ProductMovement.query.filter_by(to_location_id = to_id, product_id = pr_id).first()
                
                if pm is not None:
                    pm.quantity = pm.quantity + qty
                    db.session.commit()
                else:
                    m = ProductMovement(from_location_id = None, to_location_id = to_id, product_id = pr_id, quantity = qty)
                    db.session.add(m)
                    db.session.commit()
            else:
                return render_template('moveproduct.html', locations = Locations.query.all() , products = Products.query.all(),prmn = ProductMovement.query.all(), message = "Not enough Quantity")
        elif to_id == "":
            pm = ProductMovement.query.filter_by(to_location_id = from_id , product_id = pr_id).first()
            if pm:
                if pm.quantity >= qty:
                    p = Products.query.filter_by(id = pr_id).first()
                    p.quantity = p.quantity + qty
                    pm.quantity = pm.quantity - qty
                    db.session.commit()
                else:
                    return render_template('moveproduct.html', locations = Locations.query.all() , products = Products.query.all(),prmn = ProductMovement.query.all(), message = "not enough quantity")
            else:
                return render_template('moveproduct.html', locations = Locations.query.all() , products = Products.query.all(),prmn = ProductMovement.query.all(), message = "Location not have enough quantity")
            
        else:
            fp = ProductMovement.query.filter_by(to_location_id = from_id, product_id = pr_id).first()
            if fp is not None:
                if fp.quantity >= qty :
                    tp = ProductMovement.query.filter_by(to_location_id = to_id, product_id = pr_id).first()
                    if tp is not None :
                        tp.quantity = tp.quantity + qty
                        fp.quantity = fp.quantity - qty
                        db.session.commit()
                    else:
                        fp.quantity = fp.quantity - qty
                        m = ProductMovement(from_location_id = from_id, to_location_id = to_id, product_id = pr_id, quantity = qty)
                        db.session.add(m)
                        db.session.commit()
                else:
                    return render_template('moveproduct.html', locations = Locations.query.all() , products = Products.query.all(),prmn = ProductMovement.query.all(), message = "Not enough Quantity")
            else:
                return render_template('moveproduct.html', locations = Locations.query.all() , products = Products.query.all(),prmn = ProductMovement.query.all(), message = "Location doesnt have this product")


        return render_template('moveproduct.html', locations = Locations.query.all() , products = Products.query.all(), prmn = ProductMovement.query.all())

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)