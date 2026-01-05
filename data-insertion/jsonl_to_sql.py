#!/usr/bin/env python3
"""
Convert Ashpazyar-data.jsonl to SQL INSERT statements
Compatible with Ashpazbashi backend models
Uses auto-generated IDs and name-based foreign key references
"""

import json
import re
from collections import OrderedDict
from datetime import datetime


def escape_sql_string(value):
    """Escape single quotes for SQL"""
    if value is None:
        return 'NULL'
    if isinstance(value, bool):
        return 'TRUE' if value else 'FALSE'
    if isinstance(value, (int, float)):
        return str(value)
    # Escape single quotes by doubling them
    return "'" + str(value).replace("'", "''") + "'"


def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    return text


def parse_time(taken_time):
    """Parse time from taken_time array and return prep_time and cook_time in minutes"""
    prep_time = 0
    cook_time = 0
    
    if not taken_time or not isinstance(taken_time, list):
        return 15, 30  # Default values
    
    total_minutes = 0
    for time_str in taken_time:
        if isinstance(time_str, str):
            # Look for numbers followed by دقیقه
            matches = re.findall(r'(\d+)\s*دقیقه', time_str)
            if matches:
                total_minutes += sum(int(m) for m in matches)
    
    # If we found time, split roughly 1/3 prep, 2/3 cook
    if total_minutes > 0:
        prep_time = max(10, total_minutes // 3)
        cook_time = max(20, total_minutes - prep_time)
    else:
        prep_time, cook_time = 15, 30
    
    return prep_time, cook_time


def estimate_difficulty(recipe_steps, ingredients_count):
    """Estimate difficulty based on recipe complexity"""
    total_steps = len(recipe_steps) if recipe_steps else 0
    total_length = sum(len(step) for step in recipe_steps) if recipe_steps else 0
    
    if total_steps <= 3 and total_length < 500 and ingredients_count <= 5:
        return 'easy'
    elif total_steps <= 6 and total_length < 1500 and ingredients_count <= 10:
        return 'medium'
    else:
        return 'hard'


def generate_sql(input_file, output_file, default_author_id=1):
    """
    Generate SQL INSERT statements from JSONL file
    Uses auto-generated IDs and subqueries for foreign key references
    
    Args:
        input_file: Path to Ashpazyar-data.jsonl
        output_file: Path to output SQL file
        default_author_id: Default user ID for recipes (change this to your actual user ID)
    """
    
    # Collect all unique ingredients
    all_ingredients = OrderedDict()
    recipes_data = []
    
    print(f"Reading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                record = json.loads(line.strip())
                
                # Extract ingredients
                ingredients = record.get('ingredients', {})
                canonical = record.get('canonical', [])
                
                # Use canonical names if available, otherwise use keys from ingredients
                ingredient_names = canonical if canonical else list(ingredients.keys())
                
                for ing_name in ingredient_names:
                    clean_name = clean_text(ing_name)
                    if clean_name and clean_name not in all_ingredients:
                        all_ingredients[clean_name] = {
                            'name': clean_name,
                            'description': None,
                            'unit': 'g'  # Default unit
                        }
                
                recipes_data.append(record)
                
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping line {line_num} due to JSON error: {e}")
                continue
    
    print(f"Found {len(all_ingredients)} unique ingredients")
    print(f"Found {len(recipes_data)} recipes")
    
    # Generate SQL
    sql_statements = []
    
    # SQL Header
    sql_statements.append("-- SQL INSERT statements generated from Ashpazyar-data.jsonl")
    sql_statements.append(f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sql_statements.append(f"-- Total Ingredients: {len(all_ingredients)}")
    sql_statements.append(f"-- Total Recipes: {len(recipes_data)}")
    sql_statements.append("")
    sql_statements.append("-- IMPORTANT: Run cleanup_tables.sql FIRST to clear existing data")
    sql_statements.append("")
    
    # Insert Ingredients (without specifying ID - let database auto-generate)
    sql_statements.append("-- ============================================")
    sql_statements.append("-- INSERT INGREDIENTS")
    sql_statements.append("-- ============================================")
    sql_statements.append("")
    
    for ing_name, ing_data in all_ingredients.items():
        sql_statements.append(
            f"INSERT INTO ingredients (name, description, unit, created_at, updated_at) "
            f"VALUES ({escape_sql_string(ing_data['name'])}, "
            f"{escape_sql_string(ing_data['description'])}, "
            f"{escape_sql_string(ing_data['unit'])}, "
            f"NOW(), NOW()) "
            f"ON CONFLICT (name) DO NOTHING;"
        )
    
    sql_statements.append("")
    
    # Insert Recipes (without specifying ID - let database auto-generate)
    sql_statements.append("-- ============================================")
    sql_statements.append("-- INSERT RECIPES")
    sql_statements.append("-- ============================================")
    sql_statements.append("")
    
    for record in recipes_data:
        title = clean_text(record.get('foodname', 'Untitled Recipe'))
        description = clean_text(record.get('description', ''))
        if not description:
            # Use first part of instructions as description
            recipe_steps = record.get('recipe', [])
            if recipe_steps:
                description = clean_text(recipe_steps[0][:200])  # First 200 chars
        
        instructions = '\n'.join(record.get('recipe', []))
        instructions = clean_text(instructions)
        
        prep_time, cook_time = parse_time(record.get('taken_time', []))
        
        # Estimate servings (default to 4)
        servings = 4
        
        # Estimate difficulty
        ingredients_count = len(record.get('ingredients', {}))
        difficulty = estimate_difficulty(record.get('recipe', []), ingredients_count)
        
        # Get first image URL if available
        images = record.get('images', [])
        image_url = images[0] if images else None
        
        sql_statements.append(
            f"INSERT INTO recipes (title, description, instructions, prep_time, cook_time, "
            f"servings, difficulty, image, author_id, category_id, views_count, average_rating, "
            f"ratings_count, is_public, created_at, updated_at) "
            f"VALUES ({escape_sql_string(title)}, {escape_sql_string(description)}, "
            f"{escape_sql_string(instructions)}, {prep_time}, {cook_time}, {servings}, "
            f"{escape_sql_string(difficulty)}, {escape_sql_string(image_url)}, "
            f"{default_author_id}, NULL, 0, 0.00, 0, TRUE, NOW(), NOW());"
        )
    
    sql_statements.append("")
    
    # Insert Recipe Ingredients using subqueries to get IDs by name/title
    sql_statements.append("-- ============================================")
    sql_statements.append("-- INSERT RECIPE INGREDIENTS")
    sql_statements.append("-- ============================================")
    sql_statements.append("")
    
    for record in recipes_data:
        recipe_title = clean_text(record.get('foodname', 'Untitled Recipe'))
        ingredients = record.get('ingredients', {})
        canonical = record.get('canonical', [])
        
        # Match canonical names with ingredient quantities
        ingredient_quantities = {}
        
        # First, try to match canonical names with ingredients dict
        if canonical:
            for canon_name in canonical:
                # Try to find matching key in ingredients dict
                matched = False
                for ing_key, quantity in ingredients.items():
                    if canon_name.lower() in ing_key.lower() or ing_key.lower() in canon_name.lower():
                        ingredient_quantities[canon_name] = clean_text(quantity)
                        matched = True
                        break
                if not matched:
                    ingredient_quantities[canon_name] = 'به میزان لازم'
        else:
            # Use ingredients dict directly
            for ing_name, quantity in ingredients.items():
                clean_ing_name = clean_text(ing_name)
                ingredient_quantities[clean_ing_name] = clean_text(quantity)
        
        # Insert recipe ingredients using subqueries
        for order, (ing_name, quantity) in enumerate(ingredient_quantities.items(), start=1):
            clean_ing_name = clean_text(ing_name)
            if clean_ing_name in all_ingredients:
                # Use subquery to get recipe_id and ingredient_id
                sql_statements.append(
                    f"INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, notes, \"order\") "
                    f"SELECT r.id, i.id, {escape_sql_string(quantity)}, NULL, {order} "
                    f"FROM recipes r, ingredients i "
                    f"WHERE r.title = {escape_sql_string(recipe_title)} "
                    f"AND i.name = {escape_sql_string(clean_ing_name)} "
                    f"ON CONFLICT (recipe_id, ingredient_id) DO NOTHING;"
                )
    
    sql_statements.append("")
    sql_statements.append("-- Done!")
    sql_statements.append("")
    
    # Write SQL file
    print(f"Writing SQL to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_statements))
    
    print(f"✅ Successfully generated SQL file: {output_file}")
    print(f"   - {len(all_ingredients)} ingredients")
    print(f"   - {len(recipes_data)} recipes")
    print(f"   - Recipe-ingredient relationships (counted during insert)")
    print(f"\n⚠️  IMPORTANT:")
    print(f"   1. Run cleanup_tables.sql FIRST to clear existing data")
    print(f"   2. Make sure you have a user with ID={default_author_id}")
    print(f"   3. Or update default_author_id in the script if needed")


if __name__ == '__main__':
    import sys
    
    input_file = 'Ashpazyar-data.jsonl'
    output_file = 'Ashpazyar-data.sql'
    default_author_id = 1
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    if len(sys.argv) > 3:
        default_author_id = int(sys.argv[3])
    
    generate_sql(input_file, output_file, default_author_id)
