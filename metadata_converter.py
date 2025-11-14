"""
NIC Metadata to Dublin Core and DCAT Converter
This script converts metadata from assignment.csv to Dublin Core and DCAT formats
Output formats: RDF (Turtle) and CSV
"""

import pandas as pd
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, DCTERMS, XSD, FOAF
import os
from datetime import datetime
# Add this at the very beginning, right after imports
import sys
import io

# Force UTF-8 encoding for console output
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Define namespaces
DCAT = Namespace("http://www.w3.org/ns/dcat#")
DCT = Namespace("http://purl.org/dc/terms/")
DATAGOV = Namespace("https://data.gov.in")

def parse_csv(filepath):
    """Parse the input CSV file"""
    try:
        df = pd.read_csv(filepath)
        print(f"Successfully loaded {len(df)} records from {filepath}")
        return df
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None

def normalize_frequency(freq):
    """Normalize frequency terms to standard vocabulary"""
    freq_mapping = {
        'daily': 'http://purl.org/cld/freq/daily',
        'weekly': 'http://purl.org/cld/freq/weekly',
        'monthly': 'http://purl.org/cld/freq/monthly',
        'yearly': 'http://purl.org/cld/freq/annual',
        'quarterly': 'http://purl.org/cld/freq/quarterly'
    }
    if pd.notna(freq):
        freq_lower = str(freq).lower().strip()
        return freq_mapping.get(freq_lower, freq_lower)
    return None

def parse_date(date_str):
    """Parse date string to standard format"""
    if pd.isna(date_str):
        return None
    try:
        # Try different date formats
        for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y']:
            try:
                dt = datetime.strptime(str(date_str), fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue
        return str(date_str)
    except:
        return None

def get_publisher(row):
    """Get publisher from ministry_department or state_department"""
    if pd.notna(row.get('ministry_department')):
        return str(row['ministry_department'])
    elif pd.notna(row.get('state_department')):
        return str(row['state_department'])
    return None

def get_description(row):
    """Get description from catalog_title or note"""
    if pd.notna(row.get('catalog_title')):
        desc = str(row['catalog_title'])
        if pd.notna(row.get('note')):
            desc += ". " + str(row['note'])
        return desc
    elif pd.notna(row.get('note')):
        return str(row['note'])
    return None

def create_dublin_core_graph(df):
    """Create RDF graph for Dublin Core metadata"""
    g = Graph()
    g.bind("dct", DCT)
    g.bind("dcterms", DCTERMS)
    
    dublin_data = []
    
    for idx, row in df.iterrows():
        # Create dataset URI
        node_alias = row.get('node_alias', '')
        if pd.notna(node_alias):
            dataset_uri = URIRef(f"https://data.gov.in{node_alias}")
        else:
            dataset_uri = URIRef(f"https://data.gov.in/dataset/{idx}")
        
        # Title
        if pd.notna(row.get('title')):
            g.add((dataset_uri, DCT.title, Literal(row['title'])))
        
        # Description
        desc = get_description(row)
        if desc:
            g.add((dataset_uri, DCT.description, Literal(desc)))
        
        # Issued (published_date)
        issued = parse_date(row.get('published_date'))
        if issued:
            g.add((dataset_uri, DCT.issued, Literal(issued, datatype=XSD.date)))
        
        # Modified (changed)
        modified = parse_date(row.get('changed'))
        if modified:
            g.add((dataset_uri, DCT.modified, Literal(modified, datatype=XSD.date)))
        
        # Created
        created = parse_date(row.get('created'))
        if created:
            g.add((dataset_uri, DCT.created, Literal(created, datatype=XSD.date)))
        
        # Publisher
        publisher = get_publisher(row)
        if publisher:
            g.add((dataset_uri, DCT.publisher, Literal(publisher)))
        
        # Accrual Periodicity (frequency)
        freq = normalize_frequency(row.get('frequency'))
        if freq:
            if freq.startswith('http'):
                g.add((dataset_uri, DCT.accrualPeriodicity, URIRef(freq)))
            else:
                g.add((dataset_uri, DCT.accrualPeriodicity, Literal(freq)))
        
        # Subject/Theme (sector)
        if pd.notna(row.get('sector')):
            sectors = str(row['sector']).split(';')
            for sector in sectors:
                g.add((dataset_uri, DCT.subject, Literal(sector.strip())))
        
        # Landing Page
        if pd.notna(node_alias):
            landing_page = f"https://data.gov.in{node_alias}"
            g.add((dataset_uri, DCAT.landingPage, URIRef(landing_page)))
        
        # Collect data for CSV
        dublin_data.append({
            'dataset_uri': str(dataset_uri),
            'title': row.get('title'),
            'description': desc,
            'issued': issued,
            'modified': modified,
            'created': created,
            'publisher': publisher,
            'accrualPeriodicity': freq,
            'subject': row.get('sector'),
            'landingPage': f"https://data.gov.in{node_alias}" if pd.notna(node_alias) else None
        })
    
    return g, pd.DataFrame(dublin_data)

def create_dcat_graph(df):
    """Create RDF graph for DCAT metadata"""
    g = Graph()
    g.bind("dcat", DCAT)
    g.bind("dct", DCT)
    g.bind("dcterms", DCTERMS)
    
    dcat_data = []
    
    for idx, row in df.iterrows():
        # Create dataset URI
        node_alias = row.get('node_alias', '')
        if pd.notna(node_alias):
            dataset_uri = URIRef(f"https://data.gov.in{node_alias}")
        else:
            dataset_uri = URIRef(f"https://data.gov.in/dataset/{idx}")
        
        # Dataset type
        g.add((dataset_uri, RDF.type, DCAT.Dataset))
        
        # Basic metadata (same as Dublin Core)
        if pd.notna(row.get('title')):
            g.add((dataset_uri, DCT.title, Literal(row['title'])))
        
        desc = get_description(row)
        if desc:
            g.add((dataset_uri, DCT.description, Literal(desc)))
        
        issued = parse_date(row.get('published_date'))
        if issued:
            g.add((dataset_uri, DCT.issued, Literal(issued, datatype=XSD.date)))
        
        modified = parse_date(row.get('changed'))
        if modified:
            g.add((dataset_uri, DCT.modified, Literal(modified, datatype=XSD.date)))
        
        publisher = get_publisher(row)
        if publisher:
            g.add((dataset_uri, DCT.publisher, Literal(publisher)))
        
        freq = normalize_frequency(row.get('frequency'))
        if freq:
            if freq.startswith('http'):
                g.add((dataset_uri, DCT.accrualPeriodicity, URIRef(freq)))
            else:
                g.add((dataset_uri, DCT.accrualPeriodicity, Literal(freq)))
        
        if pd.notna(row.get('sector')):
            sectors = str(row['sector']).split(';')
            for sector in sectors:
                g.add((dataset_uri, DCAT.theme, Literal(sector.strip())))
        
        if pd.notna(node_alias):
            landing_page = f"https://data.gov.in{node_alias}"
            g.add((dataset_uri, DCAT.landingPage, URIRef(landing_page)))
        
        # Distributions
        dist_counter = 1
        
        # API Distribution (datafile_url)
        if pd.notna(row.get('datafile_url')):
            dist_uri = URIRef(f"{dataset_uri}/distribution/api")
            g.add((dist_uri, RDF.type, DCAT.Distribution))
            g.add((dataset_uri, DCAT.distribution, dist_uri))
            g.add((dist_uri, DCAT.accessURL, URIRef(row['datafile_url'])))
            
            if pd.notna(row.get('file_format')):
                g.add((dist_uri, DCT['format'], Literal(row['file_format'])))
                g.add((dist_uri, DCAT.mediaType, Literal(row['file_format'])))
            
            if pd.notna(row.get('file_size')):
                try:
                    size = int(row['file_size'])
                    g.add((dist_uri, DCAT.byteSize, Literal(size, datatype=XSD.integer)))
                except:
                    pass
            
            dcat_data.append({
                'dataset_uri': str(dataset_uri),
                'distribution_uri': str(dist_uri),
                'distribution_type': 'API',
                'accessURL': row['datafile_url'],
                'downloadURL': None,
                'format': row.get('file_format'),
                'byteSize': row.get('file_size'),
                'title': row.get('title')
            })
        
        # File Download Distribution (datafile)
        if pd.notna(row.get('datafile')):
            dist_uri = URIRef(f"{dataset_uri}/distribution/file")
            g.add((dist_uri, RDF.type, DCAT.Distribution))
            g.add((dataset_uri, DCAT.distribution, dist_uri))
            g.add((dist_uri, DCAT.downloadURL, URIRef(row['datafile'])))
            
            if pd.notna(row.get('file_format')):
                g.add((dist_uri, DCT['format'], Literal(row['file_format'])))
                g.add((dist_uri, DCAT.mediaType, Literal(row['file_format'])))
            
            if pd.notna(row.get('file_size')):
                try:
                    size = int(row['file_size'])
                    g.add((dist_uri, DCAT.byteSize, Literal(size, datatype=XSD.integer)))
                except:
                    pass
            
            dcat_data.append({
                'dataset_uri': str(dataset_uri),
                'distribution_uri': str(dist_uri),
                'distribution_type': 'File',
                'accessURL': None,
                'downloadURL': row['datafile'],
                'format': row.get('file_format'),
                'byteSize': row.get('file_size'),
                'title': row.get('title')
            })
    
    return g, pd.DataFrame(dcat_data)

def main():
    """Main execution function"""
    # Create output directory
    os.makedirs('output', exist_ok=True)
    
    # Parse input CSV
    print("Step 1: Parsing input CSV...")
    df = parse_csv('assignment.csv')
    if df is None:
        return
    
    # Create Dublin Core outputs
    print("\nStep 2: Creating Dublin Core metadata...")
    dc_graph, dc_df = create_dublin_core_graph(df)
    
    # Save Dublin Core RDF (Turtle)
    dc_graph.serialize(destination='output/dublin.ttl', format='turtle')
    print("+ Created output/dublin.ttl")
    
    # Save Dublin Core CSV
    dc_df.to_csv('output/dublin.csv', index=False)
    print("+ Created output/dublin.csv")
    
    # Create DCAT outputs
    print("\nStep 3: Creating DCAT metadata...")
    dcat_graph, dcat_df = create_dcat_graph(df)
    
    # Save DCAT RDF (Turtle)
    dcat_graph.serialize(destination='output/dcat.ttl', format='turtle')
    print("+ Created output/dcat.ttl")
    
    # Save DCAT CSV
    dcat_df.to_csv('output/dcat.csv', index=False)
    print("+ Created output/dcat.csv")
    
    print("\n" + "="*50)
    print("Conversion completed successfully!")
    print("Output files created in 'output/' directory:")
    print("  - dublin.ttl (Dublin Core RDF)")
    print("  - dublin.csv (Dublin Core CSV)")
    print("  - dcat.ttl (DCAT RDF)")
    print("  - dcat.csv (DCAT CSV)")
    print("="*50)

if __name__ == "__main__":
    main()
