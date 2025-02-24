#!/usr/bin/env python3
import requests
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, SetMenu, Cuisine, SetMenuCuisineLink
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv() #Loads .env file

POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGRES_SERVER = os.environ.get("POSTGRES_SERVER")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT")
POSTGRES_DB = os.environ.get("POSTGRES_DB")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def harvest_set_menus(url, batch_size=100):
    db = SessionLocal()
    try:
        count = 0
        while url:
            logging.info(f"Fetching data from: {url}")
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            for item in data['data']:
                # Remove cuisines to handle separately
                cuisines = item.pop('cuisines')
                
                # Handle datetime
                created_at = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                item['created_at'] = created_at
                
                # Set default values for all boolean fields
                boolean_fields = [
                    'is_vegan', 'is_vegetarian', 'is_seated', 'is_standing',
                    'is_canape', 'is_mixed_dietary', 'is_meal_prep',
                    'is_halal', 'is_kosher', 'available'
                ]
                for field in boolean_fields:
                    item[field] = False if item.get(field) is None else item[field]
                
                # Set default values for numeric fields
                numeric_fields = {
                    'display_text': 0,
                    'status': 0,
                    'price_per_person': 0.0,
                    'min_spend': 0.0,
                    'number_of_orders': 0
                }
                for field, default in numeric_fields.items():
                    item[field] = default if item.get(field) is None else item[field]
                
                # Set default values for string fields
                string_fields = ['description', 'image', 'thumbnail', 'name']
                for field in string_fields:
                    item[field] = '' if item.get(field) is None else item[field]
                
                # Create and add the SetMenu object
                db_set_menu = SetMenu(**item)
                db.add(db_set_menu)
                db.flush()

                # Handle cuisines relationship
                if cuisines:
                    for cuisine in cuisines:
                        # Check if cuisine already exists
                        db_cuisine = db.query(Cuisine).filter(
                            Cuisine.id == cuisine['id']
                        ).first()
                        if not db_cuisine:
                            db_cuisine = Cuisine(**cuisine)
                            db.add(db_cuisine)
                            db.flush()
                        
                        # Create the link
                        link = SetMenuCuisineLink(
                            set_menu_id=db_set_menu.id,
                            cuisine_id=db_cuisine.id
                        )
                        db.add(link)
                
                count += 1
                if count % batch_size == 0:
                    db.commit()
                    logging.info(f"Committed batch of {batch_size} records")
            
            db.commit()  # Commit any remaining records
            
            url = data.get('links', {}).get('next')
            if url:
                logging.info("Waiting 2 seconds before next request...")
                time.sleep(2)
            
    except Exception as e:
        logging.error(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    initial_url = "https://staging.yhangry.com/booking/test/set-menus"
    harvest_set_menus(initial_url)