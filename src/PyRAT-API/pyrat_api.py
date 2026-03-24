import requests
import time
import json
from datetime import datetime
import sys
import re

# API Configuration
API_CLIENT_TOKEN = "1-9vBhAUJnGJZldlehOEKX08"
API_USER_TOKEN = "17-fc33efd511cadfec808f833f59a3516cdcf802459c70"
BASE_URL = "https://ucl.pyrat.cloud/api/v3"

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
            elif method.upper() == 'PUT':
                response = requests.put(url, **kwargs)
            elif method.upper() == 'PATCH':
                response = requests.patch(url, **kwargs)
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
    
    def extract_rfid_from_comment(self, comment_text):
        """Extract RFID value from a comment"""
        patterns = [
            r'#?RFID[_\s]*(?:Scanned)?:\s*(\d+)',
            r'rfid\s*[=:]\s*(\d+)',
            r'RFID\s+(\d{8,})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, comment_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def get_rfid_from_comments(self, animal_id):
        """Get the most recent RFID from comments"""
        comments = self.get_comments(animal_id)
        
        if not comments:
            return None
        
        sorted_comments = sorted(comments, key=lambda x: x.get('created', ''), reverse=True)
        
        for comment in sorted_comments:
            content = comment.get('content', '')
            rfid = self.extract_rfid_from_comment(content)
            if rfid:
                return rfid
        
        return None
    
    def find_animal_by_rfid(self, rfid):
        """Find an animal by RFID tag"""
        print(f"Searching for animal with RFID: {rfid}...")
        
        params = {'rfid': rfid}
        response = self.make_request('GET', 'animals', params=params)
        
        if response and response.status_code == 200:
            results = response.json()
            if results:
                print(f"Found {len(results)} animal(s) with RFID {rfid}")
                return results[0] if len(results) == 1 else results
            else:
                print(f"No animals found with RFID {rfid}")
                return None
        else:
            print(f"Search failed")
            return None
    
    def update_animal_weight(self, animal_id, weight_g, weight_time=None):
        """Update an animal's weight via API"""
        if weight_time is None:
            weight_time = datetime.utcnow().isoformat() + 'Z'
        
        print(f"Updating weight for animal {animal_id}: {weight_g}g at {weight_time}")
        
        data = {
            "weight": float(weight_g),
            "weight_time": weight_time
        }
        
        response = self.make_request('PUT', f'animals/{animal_id}/weight', json=data)
        
        if response and response.status_code in [200, 201, 204]:
            print(f"Weight updated successfully!")
            return True
        else:
            print(f"Failed to update weight: Status {response.status_code if response else 'No response'}")
            if response:
                print(f"   Response: {response.text[:500]}")
            return False
    
    def batch_update_weights(self, weight_data):
        """Update weights for multiple animals"""
        print(f"Batch updating weights for {len(weight_data)} animals...")
        
        results = {
            'successful': [],
            'failed': []
        }
        
        for item in weight_data:
            animal_id = item.get('animal_id')
            weight = item.get('weight')
            weight_time = item.get('weight_time')
            
            if not animal_id or weight is None:
                print(f"Skipping invalid entry: {item}")
                results['failed'].append(item)
                continue
            
            success = self.update_animal_weight(animal_id, weight, weight_time)
            
            if success:
                results['successful'].append(animal_id)
            else:
                results['failed'].append(animal_id)
        
        print(f"\nBatch update complete:")
        print(f"Successful: {len(results['successful'])}")
        print(f"Failed: {len(results['failed'])}")
        
        return results
    
    def get_single_mouse(self, mouse_id):
        """Get a specific mouse by ID with all associated information"""
        print(f"Fetching mouse: {mouse_id}")
        
        mouse_data = self.get_animal_by_exact_id(mouse_id)
        
        if mouse_data:
            actual_id = mouse_data.get('eartag_or_id', mouse_id)
            print(f"Found mouse: {actual_id}")
            
            mouse_info = {
                'basic_info': mouse_data,
                'comments': self.get_comments(actual_id),
                'latest_weight': self.get_latest_weight(actual_id),
                'rfid': self.get_rfid_from_comments(actual_id),
                'water_requirement': None
            }
            
            if mouse_info['latest_weight']:
                mouse_info['water_requirement'] = self.calculate_water_requirement(mouse_info['latest_weight'])
            
            return mouse_info
        else:
            print(f"Mouse '{mouse_id}' not found")
            return None
    
    def display_mouse_info(self, mouse_info):
        """Display comprehensive mouse information in a readable format"""
        if not mouse_info:
            print("No mouse information to display")
            return
        
        basic = mouse_info['basic_info']
        comments = mouse_info['comments'] or []
        latest_weight = mouse_info['latest_weight']
        water_req = mouse_info['water_requirement']
        rfid = mouse_info.get('rfid')
        
        print("MOUSE INFORMATION")

        print("\nBASIC INFORMATION:")
        for key, value in basic.items():
            if value is not None and value != "":
                print(f"{key:20}: {value}")
        
        if rfid:
            print(f"{'RFID':20}: {rfid}")
        
        print(f"\nWEIGHT & WATER:")
        print("-" * 20)
        if latest_weight:
            print(f"{'Latest Weight':20}: {latest_weight}g")
            if water_req:
                print(f"{'Water Requirement':20}: {water_req}ml/day")
        else:
            print("No weight records found")
        
        print(f"\nRECENT COMMENTS ({len(comments)} total):")
        print("-" * 20)
        if comments:
            sorted_comments = sorted(comments, key=lambda x: x.get('created', ''), reverse=True)
            
            for comment in sorted_comments[:5]:
                created = comment.get('created', 'Unknown date')
                content = comment.get('content', 'No content')
                print(f"{created}: {content}")
                
            if len(comments) > 5:
                print(f"... and {len(comments) - 5} more comments")
        else:
            print("No comments found")
        
    
    def get_animals_detailed(self, limit=None, name_filter=None, **field_filters):
        """Get animals with detailed information and flexible filtering options"""
        from urllib.parse import urlencode
        
        print(f"Fetching detailed animals (limit: {limit})...")
        
        detailed_fields = [
            'eartag_or_id', 'sex', 'responsible_fullname', 'owner_fullname',
            'age_days', 'age_weeks', 'strain_name', 'mutations', 'dateborn',
            'weight', 'cagenumber', 'room_name', 'area_name',
            'building_name', 'species_name', 'state', 'cagelabel', 'cagetype',
            'generation', 'origin_name', 'classification'
        ]
        
        params_list = []
        
        if limit:
            params_list.append(('l', str(limit)))
            
        if name_filter:
            params_list.append(('eartag_or_id', f"*{name_filter}*"))
            
        for field in detailed_fields:
            params_list.append(('k', field))
        
        endpoint = 'animals?' + urlencode(params_list, doseq=False)
        url = f"{self.base_url}/{endpoint}"
        
        response = requests.get(url, auth=self.auth, timeout=self.timeout)
        
        if response and response.status_code == 200:
            animals = response.json()
            print(f"Retrieved {len(animals)} animals with detailed info")
            
            filtered_animals = self.apply_flexible_filters(animals, field_filters)
            
            include_comments = field_filters.get('include_comments', False)
            if include_comments and filtered_animals:
                print("Fetching comments for animals...")
                for animal in filtered_animals:
                    animal_id = animal.get('eartag_or_id')
                    if animal_id:
                        animal['detailed_comments'] = self.get_comments(animal_id)
            
            return filtered_animals
        else:
            print("Failed to get detailed animals")
            if response:
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text[:500]}")
            return None
    
    def apply_flexible_filters(self, animals, field_filters):
        """Apply flexible filtering based on any field"""
        if not field_filters:
            return animals
            
        filtered = animals.copy()
        
        for filter_name, filter_value in field_filters.items():
            if filter_name == 'include_comments':
                continue
                
            if filter_name.endswith('_filter'):
                field_name = filter_name[:-7]
            else:
                field_name = filter_name
            
            actual_field_name = 'mutations' if field_name == 'mutation' else field_name
            
            print(f"Filtering by {field_name}: {filter_value}")
            
            new_filtered = []
            for animal in filtered:
                field_value = animal.get(actual_field_name)
                
                if field_value is not None:
                    if isinstance(field_value, list):
                        if field_name in ['mutations', 'mutation']:
                            match_found = False
                            
                            # Check if searching for specific mutation + grade (e.g., "Cdh23 wt")
                            filter_parts = str(filter_value).strip().split()
                            search_name = None
                            search_grade = None
                            
                            if len(filter_parts) == 2:
                                search_name = filter_parts[0].lower()
                                search_grade = filter_parts[1].lower()
                            else:
                                search_term = str(filter_value).lower()
                            
                            for mutation in field_value:
                                if isinstance(mutation, dict):
                                    mutation_name = mutation.get('mutationname', '').lower()
                                    mutation_grade = mutation.get('mutationgrade', '').lower()
                                    
                                    if search_name and search_grade:
                                        # Both name and grade specified
                                        if search_name in mutation_name and search_grade in mutation_grade:
                                            match_found = True
                                            break
                                    else:
                                        # Single search term - match either name or grade
                                        if search_term in mutation_name or search_term in mutation_grade:
                                            match_found = True
                                            break
                                else:
                                    if str(filter_value).lower() in str(mutation).lower():
                                        match_found = True
                                        break
                            
                            if match_found:
                                new_filtered.append(animal)
                        else:
                            if any(str(filter_value).lower() in str(item).lower() for item in field_value):
                                new_filtered.append(animal)
                    else:
                        if str(filter_value).lower() in str(field_value).lower():
                            new_filtered.append(animal)
            
            filtered = new_filtered
        
        if len(filtered) != len(animals):
            print(f"Filtered from {len(animals)} to {len(filtered)} animals")
            
        return filtered

    def search_animals(self, search_term, exact_match=False):
        """Search animals by name pattern or exact match"""
        if exact_match:
            print(f"Searching for exact match: '{search_term}'...")
            params = {'eartag_or_id': f"*{search_term}*"}
        else:
            print(f"Searching for pattern: '*{search_term}*'...")
            params = {'eartag_or_id': f"*{search_term}*"}
        
        response = self.make_request('GET', 'animals', params=params)
        
        if response and response.status_code == 200:
            results = response.json()
            print(f"API returned {len(results)} wildcard matches")
            
            if exact_match:
                exact_results = [r for r in results if r.get('eartag_or_id') == search_term]
                print(f"Filtered to {len(exact_results)} exact matches")
                return exact_results
            else:
                exact_results = [r for r in results if r.get('eartag_or_id') == search_term]
                if len(exact_results) == 1:
                    print(f"Auto-filtering to 1 exact match: '{exact_results[0].get('eartag_or_id')}'")
                    return exact_results
                else:
                    print(f"Returning all {len(results)} wildcard matches")
                    return results
        else:
            print("Search failed")
            return None
    
    def get_animal_by_exact_id(self, animal_id):
        """Get a single animal by exact ID match"""
        print(f"Looking up exact ID: '{animal_id}'...")
        
        response = self.make_request('GET', f'animals/{animal_id}')
        if response and response.status_code == 200:
            result = response.json()
            print(f"Direct lookup successful")
            return result
        
        print("Direct lookup failed, trying wildcard search...")
        params = {'eartag_or_id': f"*{animal_id}*"}
        response = self.make_request('GET', 'animals', params=params)
        
        if response and response.status_code == 200:
            results = response.json()
            print(f"API returned {len(results)} wildcard matches")
            
            exact_matches = [r for r in results if r.get('eartag_or_id') == animal_id]
            
            if len(exact_matches) == 1:
                print(f"Found exact match: '{exact_matches[0].get('eartag_or_id')}'")
                return exact_matches[0]
            elif len(exact_matches) > 1:
                print(f"Warning: Found {len(exact_matches)} animals with identical ID")
                return exact_matches[0]
            else:
                print(f"No exact match found for ID '{animal_id}'")
                return None
        else:
            print(f"Search failed")
            return None
    
    def calculate_water_requirement(self, weight_g):
        """Calculate water requirement: 40ml/kg/day"""
        if weight_g <= 0:
            return 0
        
        weight_kg = weight_g / 1000.0
        water_ml = weight_kg * 40.0
        
        return round(water_ml, 2)
    
    def extract_weight_from_comment(self, comment_text):
        """Extract weight value from a weight comment"""
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
        
        sorted_comments = sorted(comments, key=lambda x: x.get('created', ''), reverse=True)
        
        for comment in sorted_comments:
            content = comment.get('content', '')
            weight = self.extract_weight_from_comment(content)
            if weight:
                return weight
        
        return None
    
    def get_comments(self, animal_id):
        """Get all comments for an animal"""
        response = self.make_request('GET', f'animals/{animal_id}/comments')
        
        if response and response.status_code == 200:
            comments = response.json()
            return comments
        else:
            return None
    
    def post_comment(self, animal_id, comment_text):
        """Post a comment to an animal"""
        print(f"Posting comment to animal {animal_id}: '{comment_text}'")
        
        data = {'comment': comment_text}
        response = self.make_request('POST', f'animals/{animal_id}/comments', json=data)
        
        if response and response.status_code == 200:
            print(f"Comment posted successfully")
            return True
        else:
            print(f"Failed: Status {response.status_code if response else 'No response'}")
            if response:
                print(f"Response: {response.text[:200]}")
            return False


def print_help():
    """Print usage instructions"""
    help_text = """
PyRAT Enhanced Client - Usage Guide
=====================================

Connection Test:
    python pyrat_api.py test
    
Get Mouse Info:
    python pyrat_api.py mouse <mouse_id>
    
RFID Operations:
    python pyrat_api.py rfid <rfid_number>           - Find animal by RFID
    python pyrat_api.py rfid-scan <mouse_id>         - Get RFID from comments
    
Weight Updates:
    python pyrat_api.py weight <mouse_id> <weight_g> - Update weight
    python pyrat_api.py weight <mouse_id> <weight_g> <datetime>  - With custom datetime
    
Comments:
    python pyrat_api.py comment <mouse_id> <text>    - Post comment to animal
    
Search:
    python pyrat_api.py search <pattern>             - Search animals by pattern
    
Mutation searches
    python pyrat_api.py wt 10                        - Get wild-type mice
    python pyrat_api.py mutation het 20              - All heterozygous mice
    python pyrat_api.py mutation Cdh23 50            - All Cdh23 mutations (any grade)
    python pyrat_api.py mutation "Cdh23 wt" 50       - Only Cdh23 wild-type
    python pyrat_api.py mutation "Cdh23 het" 50      - Only Cdh23 heterozygous
    python pyrat_api.py mutation "Ai32 het" 30       - Only Ai32 heterozygous
    python pyrat_api.py mutations 100                - Discover all mutations
    
Examples:
    python pyrat_api.py test
    python pyrat_api.py mouse CBR1-05823
    python pyrat_api.py rfid 987654321
    python pyrat_api.py weight CBR1-05823 25.5
    python pyrat_api.py comment CBR1-05823 "Mouse appears healthy"
    python pyrat_api.py search BKS
    python pyrat_api.py wt 10
    python pyrat_api.py mutation het 20
    python pyrat_api.py mutations 100
"""
    print(help_text)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)
    
    command = sys.argv[1].lower()
    client = PyRATClient()
    
    if command == "help" or command == "-h" or command == "--help":
        print_help()
    
    elif command == "test":
        client.test_connection()
    
    elif command == "mouse":
        if len(sys.argv) > 2:
            mouse_id = sys.argv[2]
            if client.test_connection():
                mouse_info = client.get_single_mouse(mouse_id)
                client.display_mouse_info(mouse_info)
        else:
            print("Usage: python pyrat_api.py mouse <mouse_id>")
    
    elif command == "rfid":
        if len(sys.argv) > 2:
            rfid = sys.argv[2]
            if client.test_connection():
                animal = client.find_animal_by_rfid(rfid)
                if animal:
                    if isinstance(animal, list):
                        print(f"\nFound {len(animal)} animals:")
                        for a in animal:
                            print(f"  - {a.get('eartag_or_id')}")
                    else:
                        print(f"\nAnimal ID: {animal.get('eartag_or_id')}")
        else:
            print("Usage: python pyrat_api.py rfid <rfid_number>")
    
    elif command == "rfid-scan":
        if len(sys.argv) > 2:
            mouse_id = sys.argv[2]
            if client.test_connection():
                rfid = client.get_rfid_from_comments(mouse_id)
                if rfid:
                    print(f"RFID for {mouse_id}: {rfid}")
                else:
                    print(f"No RFID found in comments for {mouse_id}")
        else:
            print("Usage: python pyrat_api.py rfid-scan <mouse_id>")
    
    elif command == "weight":
        if len(sys.argv) > 3:
            mouse_id = sys.argv[2]
            weight_g = sys.argv[3]
            weight_time = sys.argv[4] if len(sys.argv) > 4 else None
            
            if client.test_connection():
                client.update_animal_weight(mouse_id, weight_g, weight_time)
        else:
            print("Usage: python pyrat_api.py weight <mouse_id> <weight_g> [datetime]")
            print("Example: python pyrat_api.py weight M12345 25.5")
            print("Example: python pyrat_api.py weight M12345 25.5 2025-10-06T14:30:00Z")
    
    elif command == "search":
        if len(sys.argv) > 2:
            pattern = sys.argv[2]
            if client.test_connection():
                results = client.search_animals(pattern)
                if results:
                    print(f"\nFound {len(results)} animals:")
                    for r in results[:20]:
                        print(f"  {r.get('eartag_or_id')}")
                    if len(results) > 20:
                        print(f"  ... and {len(results) - 20} more")
        else:
            print("Usage: python pyrat_api.py search <pattern>")
    
    elif command == "mutation":
        if len(sys.argv) > 2:
            mutation_term = sys.argv[2]
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
            
            if client.test_connection():
                animals = client.get_animals_detailed(limit=limit, mutation_filter=mutation_term, include_comments=False)
                if animals:
                    print(f"\nFound {len(animals)} mice with mutation matching '{mutation_term}':")
                    for animal in animals:
                        mutations = animal.get('mutations', [])
                        mutation_display = ""
                        if mutations:
                            if isinstance(mutations, list):
                                mut_strs = []
                                for mut in mutations:
                                    if isinstance(mut, dict):
                                        mut_name = mut.get('mutationname', '')
                                        mut_grade = mut.get('mutationgrade', '')
                                        mut_strs.append(f"{mut_name}({mut_grade})")
                                    else:
                                        mut_strs.append(str(mut))
                                mutation_display = ", ".join(mut_strs)
                        
                        print(f"  {animal.get('eartag_or_id'):15} - {animal.get('sex'):6} - {animal.get('strain_name')}")
                        if mutation_display:
                            print(f"    Mutations: {mutation_display}")
                else:
                    print(f"No mice found with mutation '{mutation_term}'")
        else:
            print("Usage: python pyrat_api.py mutation <mutation_term> [limit]")
            print("Examples:")
            print("  python pyrat_api.py mutation het 20")
            print("  python pyrat_api.py mutation Cre 10")
    
    elif command == "mutations":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        if client.test_connection():
            print(f"Discovering all mutations in the system (scanning {limit} animals)...")
            animals = client.get_animals_detailed(limit=limit, include_comments=False)
            
            if animals:
                all_mutations = {}
                mutation_grades = set()
                
                for animal in animals:
                    mutations = animal.get('mutations', [])
                    if mutations:
                        for mut in mutations:
                            if isinstance(mut, dict):
                                mut_name = mut.get('mutationname', '')
                                mut_grade = mut.get('mutationgrade', '')
                                if mut_name:
                                    key = f"{mut_name} ({mut_grade})"
                                    all_mutations[key] = all_mutations.get(key, 0) + 1
                                    if mut_grade:
                                        mutation_grades.add(mut_grade)
                            else:
                                mut_str = str(mut)
                                all_mutations[mut_str] = all_mutations.get(mut_str, 0) + 1
                
                print(f"Found {len(all_mutations)} unique mutation types:")
                
                sorted_mutations = sorted(all_mutations.items(), key=lambda x: (-x[1], x[0]))
                
                for mut, count in sorted_mutations:
                    print(f"  {mut:40} - {count:3} mice")
                
                if mutation_grades:
                    print(f"Mutation grades found: {', '.join(sorted(mutation_grades))}")
                else:
                    print(f"No mutation grades found")
            else:
                print("No animals found")
    
    elif command == "checkmethods":
        print("Methods in PyRATClient:")
        for method in dir(client):
            if not method.startswith('_'):
                print(f"  - {method}")
    
    elif command == "comment":
        if len(sys.argv) > 3:
            mouse_id = sys.argv[2]
            comment_text = ' '.join(sys.argv[3:])
            if client.test_connection():
                client.post_comment(mouse_id, comment_text)
        else:
            print("Usage: python pyrat_api.py comment <mouse_id> <comment_text>")
            print("Example: python pyrat_api.py comment M12345 Mouse appears healthy today")

    else:
        print(f"Unknown command: {command}")
        print("Run 'python pyrat_api.py help' for usage instructions")