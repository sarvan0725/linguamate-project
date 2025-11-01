import sqlite3
import datetime
import json
import os
from contextlib import contextmanager

class LinguamateDB:
    def __init__(self):
        self.db_path = "linguamate_storage.db"
        self.init_database()
    
    @contextmanager
    def get_db_connection(self):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def init_database(self):
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS recordings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        original_text TEXT,
                        translated_text TEXT,
                        source_language TEXT,
                        target_language TEXT,
                        audio_path TEXT,
                        timestamp DATETIME,
                        user_id TEXT DEFAULT 'default'
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_stats (
                        user_id TEXT PRIMARY KEY,
                        total_translations INTEGER DEFAULT 0,
                        favorite_source_lang TEXT,
                        favorite_target_lang TEXT,
                        last_active DATETIME
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ml_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        recording_id INTEGER,
                        complexity_score TEXT,
                        sentiment_score TEXT,
                        confidence_score INTEGER,
                        predicted_language TEXT,
                        text_length INTEGER,
                        word_count INTEGER,
                        timestamp DATETIME,
                        FOREIGN KEY (recording_id) REFERENCES recordings (id)
                    )
                ''')
                
                conn.commit()
        except sqlite3.Error as e:
            print(f"Database initialization error: {e}")
            raise
    
    def save_recording(self, original_text, translated_text, source_lang, target_lang, audio_path):
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO recordings 
                    (original_text, translated_text, source_language, target_language, audio_path, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (original_text, translated_text, source_lang, target_lang, audio_path, datetime.datetime.now()))
                
                recording_id = cursor.lastrowid
                conn.commit()
                return recording_id
        except sqlite3.Error as e:
            print(f"Error saving recording: {e}")
            return None
    
    def save_ml_analysis(self, recording_id, complexity, sentiment, confidence, predicted_lang, text_length, word_count):
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO ml_analysis 
                    (recording_id, complexity_score, sentiment_score, confidence_score, predicted_language, text_length, word_count, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (recording_id, complexity, sentiment, confidence, predicted_lang, text_length, word_count, datetime.datetime.now()))
                
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error saving ML analysis: {e}")
    
    def get_ml_insights(self):
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT AVG(confidence_score), AVG(text_length), AVG(word_count) FROM ml_analysis')
                avg_stats = cursor.fetchone()
                
                cursor.execute('SELECT sentiment_score, COUNT(*) FROM ml_analysis GROUP BY sentiment_score')
                sentiment_stats = cursor.fetchall()
                
                cursor.execute('SELECT complexity_score, COUNT(*) FROM ml_analysis GROUP BY complexity_score')
                complexity_stats = cursor.fetchall()
                
                return avg_stats, sentiment_stats, complexity_stats
        except sqlite3.Error as e:
            print(f"Error getting ML insights: {e}")
            return (None, None, None), [], []
    
    def get_all_recordings(self):
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM recordings ORDER BY timestamp DESC')
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting recordings: {e}")
            return []
    
    def get_recent_recordings(self, limit=10):
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM recordings ORDER BY timestamp DESC LIMIT ?', (limit,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting recent recordings: {e}")
            return []
    
    def update_user_stats(self, source_lang, target_lang):
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO user_stats 
                    (user_id, total_translations, favorite_source_lang, favorite_target_lang, last_active)
                    VALUES ('default', 
                            COALESCE((SELECT total_translations FROM user_stats WHERE user_id = 'default'), 0) + 1,
                            ?, ?, ?)
                ''', (source_lang, target_lang, datetime.datetime.now()))
                
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error updating user stats: {e}")