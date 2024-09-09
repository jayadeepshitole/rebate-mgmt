from app import create_app, db
import logging

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    app.run(debug=True)