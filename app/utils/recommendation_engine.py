import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
from app.models.contract import Contract
from app.models.property import Property
from app.models.interest import PropertyInterest
from app import db
from datetime import datetime
import os
import pickle

class SimpleMatrixFactorization:
    """A simple implementation of matrix factorization without external ML libraries"""
    
    def __init__(self, n_factors=20, n_iterations=50, learning_rate=0.01, regularization=0.01):
        self.n_factors = n_factors
        self.n_iterations = n_iterations
        self.learning_rate = learning_rate
        self.regularization = regularization
        self.user_mapping = {}
        self.property_mapping = {}
        self.reverse_user_mapping = {}
        self.reverse_property_mapping = {}
        self.user_factors = None
        self.property_factors = None
        self.global_bias = 0
        self.user_biases = None
        self.property_biases = None
    
    def _create_mappings(self, user_ids, property_ids):
        """Create mappings between original IDs and internal indices"""
        unique_users = sorted(set(user_ids))
        unique_properties = sorted(set(property_ids))
        
        self.user_mapping = {user_id: i for i, user_id in enumerate(unique_users)}
        self.property_mapping = {prop_id: i for i, prop_id in enumerate(unique_properties)}
        
        self.reverse_user_mapping = {i: user_id for user_id, i in self.user_mapping.items()}
        self.reverse_property_mapping = {i: prop_id for prop_id, i in self.property_mapping.items()}
        
        return len(unique_users), len(unique_properties)
    
    def fit(self, user_ids, property_ids, ratings):
        """Train the matrix factorization model"""
        # Create mappings
        n_users, n_properties = self._create_mappings(user_ids, property_ids)
        
        # Initialize factors randomly
        np.random.seed(42)
        self.user_factors = np.random.normal(0, 0.1, (n_users, self.n_factors))
        self.property_factors = np.random.normal(0, 0.1, (n_properties, self.n_factors))
        
        # Initialize biases
        self.global_bias = np.mean(ratings)
        self.user_biases = np.zeros(n_users)
        self.property_biases = np.zeros(n_properties)
        
        # Map IDs to indices
        mapped_users = [self.user_mapping[uid] for uid in user_ids]
        mapped_properties = [self.property_mapping[pid] for pid in property_ids]
        
        # Stochastic gradient descent
        for iteration in range(self.n_iterations):
            # Shuffle the data
            indices = np.arange(len(ratings))
            np.random.shuffle(indices)
            
            # Update factors
            for idx in indices:
                u = mapped_users[idx]
                i = mapped_properties[idx]
                r = ratings[idx]
                
                # Compute prediction error
                prediction = self.global_bias + self.user_biases[u] + self.property_biases[i] + \
                             np.dot(self.user_factors[u], self.property_factors[i])
                error = r - prediction
                
                # Update biases
                self.user_biases[u] += self.learning_rate * (error - self.regularization * self.user_biases[u])
                self.property_biases[i] += self.learning_rate * (error - self.regularization * self.property_biases[i])
                
                # Update factors
                user_factor_temp = self.user_factors[u].copy()
                self.user_factors[u] += self.learning_rate * (error * self.property_factors[i] - self.regularization * self.user_factors[u])
                self.property_factors[i] += self.learning_rate * (error * user_factor_temp - self.regularization * self.property_factors[i])
            
            # Reduce learning rate over time
            self.learning_rate *= 0.9
        
        return self
    
    def predict(self, user_id, property_id):
        """Predict rating for a user-property pair"""
        if user_id not in self.user_mapping or property_id not in self.property_mapping:
            return 0.5  # Default prediction
        
        u = self.user_mapping[user_id]
        i = self.property_mapping[property_id]
        
        prediction = self.global_bias + self.user_biases[u] + self.property_biases[i] + \
                     np.dot(self.user_factors[u], self.property_factors[i])
        
        # Clip prediction to [0, 1]
        return max(0, min(1, prediction))
    
    def recommend_properties(self, user_id, all_property_ids, limit=10, exclude_ids=None):
        """Recommend properties for a user"""
        if exclude_ids is None:
            exclude_ids = []
        
        if user_id not in self.user_mapping:
            return []
        
        # Filter out properties to exclude
        property_ids = [pid for pid in all_property_ids if pid not in exclude_ids]
        
        # Get predictions for all properties
        predictions = [(pid, self.predict(user_id, pid)) for pid in property_ids]
        
        # Sort by predicted rating
        predictions.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N property IDs
        return [pid for pid, _ in predictions[:limit]]
    
    def save(self, filepath):
        """Save the model to disk"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'user_mapping': self.user_mapping,
                'property_mapping': self.property_mapping,
                'reverse_user_mapping': self.reverse_user_mapping,
                'reverse_property_mapping': self.reverse_property_mapping,
                'user_factors': self.user_factors,
                'property_factors': self.property_factors,
                'global_bias': self.global_bias,
                'user_biases': self.user_biases,
                'property_biases': self.property_biases,
                'n_factors': self.n_factors
            }, f)
    
    @classmethod
    def load(cls, filepath):
        """Load a saved model from disk"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        instance = cls(n_factors=data['n_factors'])
        instance.user_mapping = data['user_mapping']
        instance.property_mapping = data['property_mapping']
        instance.reverse_user_mapping = data['reverse_user_mapping']
        instance.reverse_property_mapping = data['reverse_property_mapping']
        instance.user_factors = data['user_factors']
        instance.property_factors = data['property_factors']
        instance.global_bias = data['global_bias']
        instance.user_biases = data['user_biases']
        instance.property_biases = data['property_biases']
        
        return instance

class RecommendationEngine:
    def __init__(self):
        self.property_features = {}
        self.user_preferences = {}
        self.user_property_matrix = None
        self.property_similarity_matrix = None
        self.last_update = None
        self.mf_model = None
    
    def extract_property_features(self, property):
        """Extract numerical features from a property"""
        features = [
            property.price,
            property.area or 0,
            property.bedrooms or 0,
            property.bathrooms or 0,
            property.total_floors or 0
        ]
        
        # One-hot encode property type
        if property.property_type == 'house':
            features.extend([1, 0, 0])
        elif property.property_type == 'apartment':
            features.extend([0, 1, 0])
        elif property.property_type == 'plot':
            features.extend([0, 0, 1])
        else:
            features.extend([0, 0, 0])
            
        return np.array(features)
    
    def build_property_features(self):
        """Build feature vectors for all properties"""
        properties = Property.query.filter_by(
            is_available=True,
            is_verified=True,
            verification_status='approved'
        ).all()
        
        for prop in properties:
            self.property_features[prop.id] = self.extract_property_features(prop)
    
    def build_user_preferences(self):
        """Build user preference vectors based on interests and views"""
        # Import User here to avoid circular imports
        from app.models.user import User
        
        users = User.query.filter_by(user_type='buyer').all()
        
        for user in users:
            # Get properties user has shown interest in
            interests = PropertyInterest.query.filter_by(buyer_id=user.id).all()
            interested_property_ids = [interest.property_id for interest in interests]
            
            # Get user's explicit preferences
            explicit_preferences = np.array([
                user.min_price or 0,
                user.max_price or 0,
                user.min_bedrooms or 0,
                1 if user.preferred_property_type == 'house' else 0,
                1 if user.preferred_property_type == 'apartment' else 0,
                1 if user.preferred_property_type == 'plot' else 0
            ])
            
            # Combine explicit and implicit preferences
            self.user_preferences[user.id] = {
                'explicit': explicit_preferences,
                'interested_properties': interested_property_ids
            }
    
    def build_user_property_matrix(self):
        """Build user-property interaction matrix for collaborative filtering"""
        users = list(self.user_preferences.keys())
        properties = list(self.property_features.keys())
        
        # Initialize matrix with zeros
        matrix = np.zeros((len(users), len(properties)))
        
        # Fill matrix with interactions
        for i, user_id in enumerate(users):
            interested_properties = self.user_preferences[user_id]['interested_properties']
            for prop_id in interested_properties:
                if prop_id in properties:
                    j = properties.index(prop_id)
                    matrix[i, j] = 1
        
        self.user_property_matrix = matrix
        return users, properties
    
    def build_property_similarity_matrix(self):
        """Build property similarity matrix for content-based filtering"""
        property_ids = list(self.property_features.keys())
        feature_matrix = np.array([self.property_features[pid] for pid in property_ids])
        
        # Normalize features
        feature_matrix = (feature_matrix - np.mean(feature_matrix, axis=0)) / np.std(feature_matrix, axis=0)
        
        # Replace NaN with 0
        feature_matrix = np.nan_to_num(feature_matrix)
        
        # Calculate similarity
        self.property_similarity_matrix = cosine_similarity(feature_matrix)
        return property_ids
    
    def get_content_based_recommendations(self, user_id, limit=10):
        """Get content-based recommendations for a user"""
        # Check if property_similarity_matrix exists or is None
        if self.property_similarity_matrix is None or len(self.property_similarity_matrix) == 0:
            property_ids = self.build_property_similarity_matrix()
        else:
            property_ids = list(self.property_features.keys())
        
        user_prefs = self.user_preferences.get(user_id)
        if not user_prefs or not user_prefs['interested_properties']:
            return []
        
        # Get properties user has interacted with
        user_properties = user_prefs['interested_properties']
        
        # Calculate recommendation scores
        scores = defaultdict(float)
        for prop_id in user_properties:
            if prop_id in property_ids:
                idx = property_ids.index(prop_id)
                for i, similar_prop_id in enumerate(property_ids):
                    if similar_prop_id not in user_properties:
                        scores[similar_prop_id] += self.property_similarity_matrix[idx, i]
        
        # Sort by score
        recommended_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [pid for pid, score in recommended_ids]
    
    def get_collaborative_recommendations(self, user_id, limit=10):
        """Get collaborative filtering recommendations for a user"""
        if self.user_property_matrix is None or len(self.user_property_matrix) == 0:
            users, properties = self.build_user_property_matrix()
        else:
            users = list(self.user_preferences.keys())
            properties = list(self.property_features.keys())
        
        if user_id not in users:
            return []
        
        user_idx = users.index(user_id)
        
        # Calculate user similarity
        user_similarity = cosine_similarity([self.user_property_matrix[user_idx]], self.user_property_matrix)[0]
        
        # Get similar users
        similar_users = [(i, sim) for i, sim in enumerate(user_similarity) if i != user_idx and sim > 0]
        similar_users.sort(key=lambda x: x[1], reverse=True)
        similar_users = similar_users[:5]  # Top 5 similar users
        
        # Get recommendations from similar users
        scores = defaultdict(float)
        for similar_user_idx, similarity in similar_users:
            for prop_idx, rating in enumerate(self.user_property_matrix[similar_user_idx]):
                if rating > 0 and self.user_property_matrix[user_idx][prop_idx] == 0:
                    scores[properties[prop_idx]] += similarity * rating
        
        # Sort by score
        recommended_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [pid for pid, score in recommended_ids]
    
    def get_location_based_recommendations(self, user, limit=10):
        """Get location-based recommendations (existing functionality)"""
        if not user.preferred_latitude or not user.preferred_longitude:
            return []
        
        max_distance = user.preferred_proximity or 10.0
        
        # Get properties that don't have contracts
        query = Property.query.filter(
            Property.is_available == True,
            Property.is_verified == True,
            Property.verification_status == 'approved',
            Property.user_id != user.id,
            ~Property.id.in_(
                db.session.query(Contract.property_id).filter(
                    Contract.status.in_(['pending', 'active', 'approved'])
                )
            )
        )
        
        if user.preferred_property_type:
            query = query.filter(Property.property_type == user.preferred_property_type)
        
        if user.min_price:
            query = query.filter(Property.price >= user.min_price)
        if user.max_price:
            query = query.filter(Property.price <= user.max_price)
        
        properties = query.all()
        recommended = []
        
        for prop in properties:
            if not prop.latitude or not prop.longitude:
                continue
            
            distance = prop.distance_to(user.preferred_latitude, user.preferred_longitude)
            if distance <= max_distance:
                score = 1 - (distance / max_distance)
                recommended.append((prop.id, score))
        
        recommended.sort(key=lambda x: x[1], reverse=True)
        return [pid for pid, score in recommended[:limit]]
    
    def build_matrix_factorization_model(self):
        """Build and train a matrix factorization model"""
        # First, ensure we have the user-property matrix
        if self.user_property_matrix is None:
            users, properties = self.build_user_property_matrix()
        else:
            users = list(self.user_preferences.keys())
            properties = list(self.property_features.keys())
        
        # Prepare training data
        user_ids = []
        property_ids = []
        ratings = []
        
        for user_idx, user_id in enumerate(users):
            for prop_idx, prop_id in enumerate(properties):
                # Add positive examples (interactions)
                if self.user_property_matrix[user_idx, prop_idx] > 0:
                    user_ids.append(user_id)
                    property_ids.append(prop_id)
                    ratings.append(1.0)
                
                # Add some negative examples (non-interactions)
                # We'll sample a subset to balance the dataset
                elif np.random.random() < 0.1:  # 10% sampling rate for negative examples
                    user_ids.append(user_id)
                    property_ids.append(prop_id)
                    ratings.append(0.0)
        
        # Create and train the model
        self.mf_model = SimpleMatrixFactorization(
            n_factors=20,
            n_iterations=50,
            learning_rate=0.01,
            regularization=0.01
        )
        
        self.mf_model.fit(user_ids, property_ids, ratings)
        
        # Save the model
        model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models')
        os.makedirs(model_dir, exist_ok=True)
        self.mf_model.save(os.path.join(model_dir, 'simple_mf_model.pkl'))
        
        return self.mf_model
    
    def get_matrix_factorization_recommendations(self, user_id, limit=10):
        """Get recommendations using the matrix factorization model"""
        # Check if model exists
        if not self.mf_model:
            try:
                model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                         'models', 'simple_mf_model.pkl')
                if os.path.exists(model_path):
                    self.mf_model = SimpleMatrixFactorization.load(model_path)
                else:
                    self.build_matrix_factorization_model()
            except Exception as e:
                print(f"Error loading matrix factorization model: {e}")
                return []
        
        # Get all property IDs
        property_ids = list(self.property_features.keys())
        
        # Get properties the user has already interacted with
        user_properties = self.user_preferences.get(user_id, {}).get('interested_properties', [])
        
        # Get recommendations
        try:
            recommended_ids = self.mf_model.recommend_properties(
                user_id, 
                property_ids, 
                limit=limit, 
                exclude_ids=user_properties
            )
            return recommended_ids
        except Exception as e:
            print(f"Error getting matrix factorization recommendations: {e}")
            return []
    
    def get_hybrid_recommendations(self, user_id, limit=10):
        """Combine all recommendation methods for hybrid recommendations"""
        # Import User here to avoid circular imports
        from app.models.user import User
        
        # Initialize engine if needed
        if not self.property_features:
            self.build_property_features()
        if not self.user_preferences:
            self.build_user_preferences()
        
        user = User.query.get(user_id)
        if not user:
            return []
        
        # Get recommendations from each method
        content_recs = self.get_content_based_recommendations(user_id, limit=limit)
        collab_recs = self.get_collaborative_recommendations(user_id, limit=limit)
        location_recs = self.get_location_based_recommendations(user, limit=limit)
        
        # Get matrix factorization recommendations if available
        mf_recs = []
        try:
            mf_recs = self.get_matrix_factorization_recommendations(user_id, limit=limit)
        except Exception as e:
            print(f"Error getting matrix factorization recommendations: {e}")
        
        # Combine and weight recommendations
        scores = defaultdict(float)
        
        # Weight: 30% content, 20% collaborative, 30% location, 20% matrix factorization
        for pid in content_recs:
            scores[pid] += 0.3 * (1 - content_recs.index(pid) / len(content_recs) if content_recs else 0)
        
        for pid in collab_recs:
            scores[pid] += 0.2 * (1 - collab_recs.index(pid) / len(collab_recs) if collab_recs else 0)
        
        for pid in location_recs:
            scores[pid] += 0.3 * (1 - location_recs.index(pid) / len(location_recs) if location_recs else 0)
        
        for pid in mf_recs:
            scores[pid] += 0.2 * (1 - mf_recs.index(pid) / len(mf_recs) if mf_recs else 0)
        
        # Sort by final score
        recommended_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]
        property_ids = [pid for pid, score in recommended_ids]
        
        # Fetch property objects
        return Property.query.filter(Property.id.in_(property_ids)).all()

# Create a singleton instance
recommendation_engine = RecommendationEngine() 