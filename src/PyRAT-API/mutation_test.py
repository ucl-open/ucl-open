import requests
import time
import json
from datetime import datetime
import sys
import re

# API Configuration
API_CLIENT_TOKEN = "1-0551cc75b1b0c60b96d321857ac2bfd331e950e3f3c7"
API_USER_TOKEN = "18-003fedaa38df0539987b74fdb766abe95ec49830bc15"
BASE_URL = "https://ucl-uat.pyrat.cloud/api/v3"

class PyRATClient:
    def __init__(self):
        self.base_url = BASE_URL
        self.auth = (API_CLIENT_TOKEN, API_USER_TOKEN)
        self.timeout = 30
        
    def make_request(self, method, endpoint, **kwargs):
        """Make a request with consistent error handling"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        kwargs.setdefault('timeout', self.timeout)
        kwargs['auth'] = self.auth
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, **kwargs)
            elif method.upper() == 'POST':
                response = requests.post(url, **kwargs)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
        except requests.exceptions.Timeout:
            print(f"Request timed out after {self.timeout}s")
            return None
        except requests.exceptions.ConnectionError:
            print(f"Connection error - check network/VPN")
            return None
        except Exception as e:
            print(f"Request failed: {e}")
            return None
    
    def test_connection(self):
        """Test API connection"""
        print("Testing connection...")
        response = self.make_request('GET', 'version')
        
        if response and response.status_code == 200:
            data = response.json()
            print(f"Connected to PyRAT {data['pyrat_version']}")
            return True
        else:
            print("Connection failed")
            return False
    
    def get_animals(self, limit=10, name_filter=None):
        """Get animals with simple filtering"""
        print(f"Fetching {limit} animals...")
        
        params = {'l': limit}
        if name_filter:
            params['eartag_or_id'] = f"*{name_filter}*"
            
        response = self.make_request('GET', 'animals', params=params)
        
        if response and response.status_code == 200:
            animals = response.json()
            print(f"Found {len(animals)} animals")
            return animals
        else:
            print("Failed to get animals")
            if response:
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
            return None
        """Test access to both mutation and genotype fields"""
        print("TESTING FIELD ACCESS")
        print("=" * 30)
        
        animals = self.get_animals(limit=5)
        if animals:
            for i, animal in enumerate(animals):
                print(f"Animal {i+1}: {animal.get('eartag_or_id', 'Unknown')}")
                print(f"  mutation: {animal.get('mutation', 'NOT FOUND')}")
                print(f"  genotype: {animal.get('genotype', 'NOT FOUND')}")
                print("---")
        
        return animals
        """Get animals with simple filtering (mutation filtering NOT supported by API)"""
        print(f"Fetching {limit} animals...")
        
        params = {'l': limit}
        if name_filter:
            params['eartag_or_id'] = f"*{name_filter}*"
            
        response = self.make_request('GET', 'animals', params=params)
        
        if response and response.status_code == 200:
            animals = response.json()
            print(f"Found {len(animals)} animals")
            return animals
        else:
            print("Failed to get animals")
            if response:
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
            return None
    
    def search_animals(self, search_term):
        """Search animals by name pattern"""
        print(f"Searching for '{search_term}'...")
        
        params = {'eartag_or_id': f"*{search_term}*"}
        response = self.make_request('GET', 'animals', params=params)
        
        if response and response.status_code == 200:
            results = response.json()
            print(f"Found {len(results)} matching animals")
            return results
        else:
            print("Search failed")
            return None
    
    def calculate_water_requirement(self, weight_g):
        """Calculate water requirement: 40ml/kg/day"""
        if weight_g <= 0:
            return 0
        
        weight_kg = weight_g / 1000.0
        water_ml = weight_kg * 40.0  # 40ml/kg/day
        
        return round(water_ml, 2)
    
    def extract_weight_from_comment(self, comment_text):
        """Extract weight value from a weight comment"""
        # Look for patterns like "#Weight_Recorded: 25.0g" or "Weight: 25g"
        patterns = [
            r'#Weight_Recorded:\s*(\d+\.?\d*)g',
            r'Weight:\s*(\d+\.?\d*)g',
            r'weight:\s*(\d+\.?\d*)g',
            r'(\d+\.?\d*)g'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, comment_text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def get_latest_weight(self, animal_id):
        """Get the most recent weight from comments"""
        comments = self.get_comments(animal_id)
        
        if not comments:
            return None
        
        # Sort by creation date, most recent first
        sorted_comments = sorted(comments, key=lambda x: x.get('created', ''), reverse=True)
        
        for comment in sorted_comments:
            content = comment.get('content', '')
            weight = self.extract_weight_from_comment(content)
            if weight:
                print(f"Found latest weight: {weight}g from comment: {content[:50]}...")
                return weight
        
        print("No weight found in comments")
        return None
    
    def auto_calculate_and_post_water(self, animal_id):
        """Automatically calculate water based on latest weight and post recommendation"""
        print(f"Auto-calculating water for animal {animal_id}...")
        
        # Get latest weight
        weight = self.get_latest_weight(animal_id)
        
        if not weight:
            print("Cannot calculate water - no weight found")
            return False
        
        # Calculate water requirement
        water_ml = self.calculate_water_requirement(weight)
        
        print(f"Calculated water requirement: {water_ml}ml/day for {weight}g mouse")
        
        # Post water calculation comment
        comment = f"#Water_Calculated: {water_ml}ml/day (based on {weight}g @ 40ml/kg/day)"
        success = self.post_comment(animal_id, comment)
        
        if success:
            print(f"Water calculation posted successfully")
        
        return success
    
    def post_comment(self, animal_id, comment_text):
        """Post a comment to an animal"""
        print(f"Posting comment to animal {animal_id}: '{comment_text}'")
        
        data = {'comment': comment_text}
        response = self.make_request('POST', f'animals/{animal_id}/comments', json=data)
        
        if response and response.status_code == 200:
            print(f"SUCCESS! Comment posted")
            return True
        else:
            print(f"FAILED: Status {response.status_code if response else 'No response'}")
            if response:
                print(f"Response: {response.text[:200]}")
            return False
    
    def post_water_delivery(self, animal_id, volume_ml):
        """Post water delivery comment"""
        comment = f"#Water_Delivery: {volume_ml}ml"
        return self.post_comment(animal_id, comment)
    
    def post_weight_record(self, animal_id, weight_g):
        """Post weight record comment and auto-calculate water"""
        # Post the weight
        comment = f"#Weight_Recorded: {weight_g}g"
        success = self.post_comment(animal_id, comment)
        
        if success:
            # Auto-calculate and post water requirement
            time.sleep(0.5)  # Small delay
            self.auto_calculate_and_post_water(animal_id)
        
        return success
    
    def post_implant_weight(self, animal_id, weight_g):
        """Post implant weight comment"""
        comment = f"#Implant_Weight: {weight_g}g"
        return self.post_comment(animal_id, comment)
    
    def get_comments(self, animal_id):
        """Get all comments for an animal"""
        response = self.make_request('GET', f'animals/{animal_id}/comments')
        
        if response and response.status_code == 200:
            comments = response.json()
            return comments
        else:
            return None
    
    def delete_comment(self, animal_id, comment_id):
        """Delete a specific comment"""
        response = self.make_request('DELETE', f'animals/{animal_id}/comments/{comment_id}')
        
        if response and response.status_code in [200, 204]:
            return True
        else:
            return False
    
    def benchmark_performance(self, num_requests=5):
        """Simple performance benchmark"""
        print(f"Benchmarking {num_requests} requests...")
        
        times = []
        for i in range(num_requests):
            start = time.time()
            response = self.make_request('GET', 'animals', params={'l': 10})
            end = time.time()
            
            if response and response.status_code == 200:
                times.append(end - start)
                print(f"   Request {i+1}: {end-start:.3f}s")
            else:
                print(f"   Request {i+1}: Failed")
        
        if times:
            avg = sum(times) / len(times)
            print(f"Average response time: {avg:.3f}s")
            return avg
        else:
            print("All requests failed")
            return None

def demo_working_features():
    """Demonstrate only the features that actually work"""
    print("WORKING FEATURES DEMO")
    print("=" * 40)
    
    client = PyRATClient()
    
    if not client.test_connection():
        return
    
    # Demo 1: Basic animal retrieval and filtering
    print("\n1. ANIMAL RETRIEVAL & NAME FILTERING")
    print("-" * 40)
    animals = client.get_animals(limit=5)
    if animals:
        print("Sample animals:")
        for animal in animals[:3]:
            print(f"   {animal.get('eartag_or_id', 'Unknown')}")
    
    # Test name filtering
    animals_with_m = client.search_animals("M")
    
    # Demo 2: Water calculation system
    print("\n2. WATER CALCULATION SYSTEM")
    print("-" * 30)
    test_weights = [20, 25, 30, 35]
    for weight in test_weights:
        water = client.calculate_water_requirement(weight)
        print(f"   {weight}g mouse → {water}ml/day")
    
    # Demo 3: Comment system with auto water calculation
    print("\n3. AUTOMATED WEIGHT + WATER POSTING")
    print("-" * 40)
    animals = client.get_animals(limit=3)
    if animals:
        animal_id = animals[0].get('eartag_or_id')
        if animal_id:
            print(f"Testing with animal: {animal_id}")
            
            # Post a weight and auto-calculate water
            print("Posting weight record with auto water calculation...")
            client.post_weight_record(animal_id, 27.5)
    
    # Demo 4: Performance benchmark
    print("\n4. PERFORMANCE BENCHMARK")
    print("-" * 25)
    client.benchmark_performance(3)
    
    print("\n" + "=" * 40)
    print("SUMMARY - What works:")
    print("✓ Animal retrieval with limits")
    print("✓ Name-based search/filtering") 
    print("✓ Water calculation (40ml/kg/day)")
    print("✓ Comment posting system")
    print("✓ Automated weight → water calculation")
    print("✓ Performance benchmarking")
    print("\nWhat doesn't work:")
    print("✗ Mutation/genotype data access via API")
    print("✗ WT mice counting (requires web interface)")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "demo":
            demo_working_features()
        else:
            print("Usage: python pyrat_api.py [demo]")
    else:
        demo_working_features()