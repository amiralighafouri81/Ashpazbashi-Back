-- Cleanup script: Delete all data from recipe-related tables
-- KEEPS: users table and user_profiles table
-- Run this BEFORE importing new data

-- Disable foreign key checks temporarily (PostgreSQL doesn't support this, but we'll delete in order)
-- For PostgreSQL, we need to delete in the correct order due to foreign key constraints

BEGIN;

-- Delete in order: child tables first, then parent tables

-- Recipe-related junction and child tables
DELETE FROM recipe_ingredients;
DELETE FROM recipe_ratings;
DELETE FROM recipe_generations;
DELETE FROM bookmarks;
DELETE FROM recipe_history;
DELETE FROM recipe_shares;

-- Nutrition tables
DELETE FROM ingredient_nutrition;
DELETE FROM nutrition;

-- Ingredient substitutes
DELETE FROM ingredient_substitutes;

-- Recipes (parent table for many relationships)
DELETE FROM recipes;

-- Ingredients
DELETE FROM ingredients;

-- Many-to-many relationship tables (Django auto-generated)
DELETE FROM recipes_tags;
DELETE FROM recipes_dietary_types;

-- Categories (optional - only if you want to clear them too)
-- Uncomment if you want to clear categories, tags, and dietary types:
-- DELETE FROM tags;
-- DELETE FROM dietary_types;
-- DELETE FROM categories;

-- Reset sequences (PostgreSQL)
-- This ensures new inserts start from 1
SELECT setval('recipe_ingredients_id_seq', 1, false);
SELECT setval('recipe_ratings_id_seq', 1, false);
SELECT setval('recipe_generations_id_seq', 1, false);
SELECT setval('bookmarks_id_seq', 1, false);
SELECT setval('recipe_history_id_seq', 1, false);
SELECT setval('nutrition_id_seq', 1, false);
SELECT setval('ingredient_nutrition_id_seq', 1, false);
SELECT setval('ingredient_substitutes_id_seq', 1, false);
SELECT setval('recipes_id_seq', 1, false);
SELECT setval('ingredients_id_seq', 1, false);

COMMIT;

-- Note: Users and user_profiles are NOT deleted
-- Make sure you have at least one user with ID=1 (or update the SQL file to use a different user ID)

