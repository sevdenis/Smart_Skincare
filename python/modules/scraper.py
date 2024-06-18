import pandas as pd
import requests
import json
import os
from bs4 import BeautifulSoup


export_folder_name = 'export'
current_dir = os.getcwd()
export_path = os.path.join(current_dir, export_folder_name)

if not os.path.exists(export_path):
    os.makedirs(export_path)

def get_brand_links(results=False, export_brand_links=True):
    url = ('https://www.cultbeauty.co.uk/brands.list')
    page = requests.get(url)
    if page.status_code == 200:
        print(f'Brands page successfully requested, {url}')
    else:
        print(f'Request failed with status code {page.status_code}')

    soup = BeautifulSoup(page.content, 'html.parser')
    items = soup.find_all("a",{"class":"responsiveBrandsPageScroll_brand"})
    brand_links = []
    for item in items:
        brand_links.append(item.get('href'))
    
    print('Brand links collected')

    if export_brand_links:
        file_path = export_path + '/brand_links.json'
        with open(file_path, 'w') as file:
            json.dump(brand_links, file)
            
    print('Brand links exported')
    if results:
        return brand_links
    else:
        return None

def get_product_links(export_path=export_path, results=False, export_product_links=True):
    brand_links_path = export_path + '/brand_links.json'
    with open(brand_links_path, 'r') as file:
        brand_links = json.load(file)

    product_links = []
    for link in brand_links:
        page = requests.get(link)
        if page.status_code == 200:
            print(f'Brand page successfully requested, {link}')
        else:
            print(f'Brand page request failed with status code {page.status_code}')


        soup = BeautifulSoup(page.content, 'html.parser')

        shop_all = soup.find_all("a",{"class":"twoItemImageTextBlock_description_itemButton "})
        if shop_all:
            print('Shop all button detected')
            hdef = shop_all.get('hdef')
            new_brand_link = f'https://www.cultbeauty.co.uk/{hdef}'
            page = requests.get(link)
            if page.status_code == 200:
                print(f'Shop all detected, brands page successfully requested again, {new_brand_link}')
            else:
                print(f'New request failed with status code {page.status_code}')
            soup = BeautifulSoup(page.content, 'html.parser')

        # Get product meta data #<a class="productBlock_link",
        items = soup.find_all("a", {"class":"productBlock_link"})
        for item in items:
            product_links.append(f'https://www.cultbeauty.co.uk/{item.get("href")}')
        print(f'Product links collected for {link}')
    print('Product link collection completed')
    if export_product_links:
            file_path = export_path + '/product_links.json'
            with open(file_path, 'w') as file:
                json.dump(product_links, file)
            print('Product links exported')

        
    if results:
        return product_links
    else:
        return None


def get_product_details(export_path=export_path, return_results=False, export_product_details=True):
    product_links_path = export_path + '/product_links.json'
    with open(product_links_path, 'r') as file:
        product_links = json.load(file)
    problem_with_detail_extraction= []
    unsuccessful_request = []


    df = pd.DataFrame(columns=['prod_id', 'site_id', 'prod_name', 'prod_price', 'prod_brand', 'prod_category',
                               'prod_img_src', 'prod_link', 'description', 'how_to_use', 'full_ingredients_list'])

    i = 0
    for link in product_links:
        df.loc[i, 'prod_link'] = link

        page = requests.get(link)
        if page.status_code == 200:
            print(f'Product page successfully requested, {link}')
            soup = BeautifulSoup(page.content, 'html.parser')

            # Get product photo
            print('Getting product details ...')
            items = soup.find_all("img", {"class": "athenaProductImageCarousel_image"})
            prod_img_src = []
            if items:
                for item in items:
                    if item != '':
                        prod_img_src.append(item.get('src'))

            df.loc[i, 'prod_img_src'] = prod_img_src

            # Get product meta-data
            try:
                items = soup.find_all("div", {"class": "athenaProductPage_productAddToBasket cta-sticky-bottom"})
                meta_data = items[0].find('span',
                                          {'data-product-id': True, 'data-site-id': True, 'data-product-name': True,
                                           'data-product-price': True, 'data-product-category': True})
                df.loc[i, 'prod_id'] = meta_data['data-product-id']
                df.loc[i, 'site_id'] = meta_data['data-site-id']
                df.loc[i, 'prod_name'] = meta_data['data-product-name']
                df.loc[i, 'prod_price'] = meta_data['data-product-price']
                df.loc[i, 'prod_brand'] = meta_data['data-product-brand']
                df.loc[i, 'prod_category'] = meta_data['data-product-category']
            except Exception as e:
                print(e)

            # Get product details
            items = soup.find_all("div", {"class": "athenaProductPage_productDescriptionFull"})
            # Cols
            # filter_cols = items[0].find_all("div", {"class": "productDescription_contentPropertyHeading "
            #                                              "productDescription_contentPropertyHeading-tabbed"})
            # cols = tuple(x.get('data-tab-title') for x in filter_cols)
            # cols = cols[1:4]
            # Product description, how to use, full ingredient list
            details = items[0].find_all("div", {"class": "athenaProductPageSynopsisContent"})[1:]

            for col, detail in zip(['description', 'how_to_use', 'full_ingredients_list'], details):
                try:
                    df.loc[i, col] = str(detail.find_all('p')[0])[3:-4]
                except:
                    try:
                        detail = str(detail).replace('p&gt;', '<p>').replace('</div>', '</p></div>')
                        detail = BeautifulSoup(detail, 'html.parser')
                        df.loc[i, col] = str(detail.find_all('p')[0])[3:-4]
                    except:
                        print(f'Problem with detail extaction {link}')
                        problem_with_detail_extraction.append(meta_data['data-product-name'])
                        continue




            print('Product details collection is completed.')
            i = i + 1
        else:
            unsuccessful_request.append(link)
            print(f'Product  page request failed with status code {page.status_code}')


    if export_product_details:
        file_path = export_path + '/product_details.csv'
        df.to_csv(file_path)
        print('Product details exported')




