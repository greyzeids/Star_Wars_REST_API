"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planets, PeopleFavorite, PlanetFavorite
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)


@app.route('/users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    users_list = list(map(lambda user : user.serialize(), users))
    return jsonify(users_list), 200

@app.route('/users/<int:user_id>', methods = ['GET'])
def get_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return jsonify({ "info" : "Not Found"}), 404
    
    response = user.serialize()
    response["favorite"] = list(map(lambda planet : planet.serialize(), user.favorite_planets))+list(map(lambda planet : planet.serialize(), user.favorite_people))

    return jsonify(response), 200

@app.route('/users', methods = ['POST'])
def create_user():
    user_body = request.get_json()
    user_db = User(
        username = user_body["username"],
        email = user_body["email"],
        password = user_body["password"],
        is_active = user_body["is_active"]
    )
    db.session.add(user_db)
    db.session.commit()
    return jsonify(user_db.serialize()), 201
    


'''
People Endpoints

'''

@app.route('/people', methods=['GET'])
def get_people_list():
    people_db = People.query.all()
    people_list = list(map(lambda people : people.serialize(), people_db))
    return jsonify(people_list), 200

@app.route('/people/<int:people_id>', methods = ['GET'])
def get_people(people_id):
    people = People.query.filter_by(id=people_id).first()
    if people is None:
        return jsonify({ "info" : "Not Found"}), 404
    return jsonify(people.serialize()), 200

@app.route('/favorite/people/<int:people_id>', methods = ['POST'])
def add_favorite_people(people_id):
    favorite_body = request.json
    people_favorite = PeopleFavorite(user_id=favorite_body["user_id"], people_db=people_id)
    db.session.add(people_favorite)
    db.session.commit()
    response_body = {
        "msg" : "character successfully added"
    }
    return jsonify(response_body), 200

@app.route('/favorite/people/<int:id>', methods=['DELETE'])
def delete_favorite_people(id):
    favorite = PeopleFavorite.query.filter_by(user_id=1, people_db=id).first()
    
    if favorite is None:
        return jsonify({"message": "Favourite planet successfully eliminated"}), 404
    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"message": "Favourite character successfully eliminated"}), 200

'''
Planets Endpoints

'''

@app.route('/planets', methods=['GET'])
def get_planets_list():
    planets_db = Planets.query.all()
    planets_list = list(map(lambda planet : planet.serialize(), planets_db))
    return jsonify(planets_list), 200

@app.route('/planets/<int:planets_id>', methods = ['GET'])
def get_planets(planets_id):
    planet = Planets.query.filter_by(id=planets_id).first()
    if planet is None:
        return jsonify({ "info" : "Not Found"}), 404
    return jsonify(planet.serialize()), 200

@app.route('/favorite/planet/<int:planet_id>', methods = ['POST'])
def add_favorite_planet(planet_id):
    favorite_body = request.json
    planet_favorite = PlanetFavorite(user_id=favorite_body["user_id"], planet_db=planet_id)
    db.session.add(planet_favorite)
    db.session.commit()
    response_body = {
        "msg" : "character successfully added"
    }
    return jsonify(response_body), 200

@app.route('/favorite/planet/<int:id>', methods=['DELETE'])
def delete_favorite_planet(id):
    favorite = PlanetFavorite.query.filter_by(user_id=1, planet_db=id).first()
    if favorite is None:
        return jsonify({"message": "Favorite Planet not found"}), 404
    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"message": "Favorite Planet deleted to favorite"}), 200


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)