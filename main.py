from flask import Flask, jsonify, render_template, request
import pandas as pd
import re
from io import StringIO
from gemini import invoke
import markdown

app = Flask(__name__)

def get_line_by_id(search_id,file_path = "product_filtered.csv"):
    # Load the CSV file into a DataFrame
    df = pd.read_csv(file_path)
    
    result = df[df['id'] == search_id]
    
    if not result.empty:
        return result.to_dict(orient='records')[0]
    else:
        return None

def convert_dict_to_csv_string(data):
    if not data:
        raise ValueError("Data cannot be empty")
    
    # Create DataFrame and convert to CSV string
    df = pd.DataFrame(data)
    output = StringIO()
    df.to_csv(output, index=False)
    return output.getvalue()
# Load the products from CSV
def load_products():
    return pd.read_csv('product_filtered.csv').to_dict(orient='records')

@app.route('/')
def index():
    categories = ['shirt', 'shorts', 'jeans', 'trousers']
    return render_template('index.html', categories=categories)

@app.route('/api/products', methods=['GET'])
def get_products():
    category = request.args.get('category', None)
    search = request.args.get('search', None)
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    products = load_products()

    if category:
        products = [product for product in products if product['sub_categ'].lower() == category.lower()]
    
    if search:
        # Split search terms by space and create a regex pattern
        search_terms = search.lower().split()
        pattern = re.compile('|'.join([re.escape(term) for term in search_terms]), re.IGNORECASE)
        products = [product for product in products if pattern.search(product['pdt_name'])]
    
    # Pagination logic
    start = (page - 1) * limit
    end = start + limit
    paginated_products = products[start:end]
    # Optionally include total count in headers
    response = jsonify(paginated_products)
    response.headers['X-Total-Count'] = len(products)
    return response

@app.route('/api/compare', methods=['POST'])
def compare_products():
    data = request.json
    selected_products = data.get('products', [])
    if len(selected_products)<=0:
        comparison_result = markdown.markdown("please select some products to compare")
        return jsonify({'html': comparison_result})
    for prod in selected_products:
        del prod['pdt_url']
        del prod['pdt_img']
        
    selected_products = convert_dict_to_csv_string(selected_products)
    resp = invoke({"q":"compare to recommend a product and explain the user why it was reommended among the products ,","p":selected_products})
    response_content = markdown.markdown(resp.get('message',"## An Error occured"))
    
    if resp.get("pid", 0) != 0:
        product = get_line_by_id(resp.get("pid"))
        
        if product:
            product_addition = f'''
            <div class="chat-message product-showcase">
                <img src="{product.get('pdt_img', 'https://via.placeholder.com/150')}" alt="Product Image" class="product-img">
                <div class="product-details">
                    <h2 class="product-name">{product.get('pdt_name', 'Product Name')}</h2>
                    <p class="product-category">{product.get('pdt_categ', 'Product Category')}</p>
                    <p class="product-price">${product.get('price', '123.45')}</p>
                </div>
            </div>
            '''
            response_content += product_addition
            print(response_content)
    return jsonify({'html': response_content})

@app.route('/api/send-message', methods=['POST'])
def send_message():
    data = request.json
    selected_products = data.get('products', [])
    message = data.get('message', '')
    prev_chat = data.get("chat")
    
    print(prev_chat)
    resp = invoke({"q":message,"p":selected_products},prev = prev_chat)
    result = markdown.markdown(resp.get('message',"## An Error occured"))
    response_content = markdown.markdown(result)
    if resp.get("pid",0)!=0:
        product = get_line_by_id(resp.get("pid"))
        
        if product:
            product_addition = f'''
            <div class="chat-message product-showcase">
                <img src="{product.get('pdt_img', 'https://via.placeholder.com/150')}" alt="Product Image" class="product-img">
                <div class="product-details">
                    <h2 class="product-name">{product.get('pdt_name', 'Product Name')}</h2>
                    <p class="product-category">{product.get('pdt_categ', 'Product Category')}</p>
                    <p class="product-price">${product.get('price', '123.45')}</p>
                </div>
            </div>
            '''
            response_content += product_addition
            print(response_content)
    return jsonify({'html': response_content})

if __name__ == '__main__':
    app.run(debug=True)
