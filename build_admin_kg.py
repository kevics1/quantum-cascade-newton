import psycopg2
import networkx as nx
import json
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = "5432"
DB_USER = "postgres"
DB_PASS = os.environ.get("PGPASSWORD", "gis2023")
DB_NAME = "Administrator"

def connect_db():
    """Connect to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            dbname=DB_NAME
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def build_knowledge_graph():
    """Build a knowledge graph of administrative regions using NetworkX."""
    conn = connect_db()
    if not conn:
        return None

    G = nx.DiGraph()
    cursor = conn.cursor()

    logger.info("Extracting province nodes...")
    # Get provinces
    cursor.execute('SELECT "省级码", "省", "省类型" FROM province WHERE "省级码" IS NOT NULL')
    provinces = cursor.fetchall()
    for code, name, ptype in provinces:
        if code:
            G.add_node(code, name=name, level="province", type=ptype)

    logger.info("Extracting city nodes and relationships...")
    # Get cities and link to provinces
    cursor.execute('SELECT "地级码", "地名", "地级类", "省级码" FROM city WHERE "地级码" IS NOT NULL')
    cities = cursor.fetchall()
    for code, name, ctype, parent_code in cities:
        if code:
            G.add_node(code, name=name, level="city", type=ctype)
            if parent_code:
                G.add_edge(code, parent_code, type="BELONGS_TO")

    logger.info("Extracting county nodes and relationships...")
    # Get counties and link to cities
    cursor.execute('SELECT "县级码", "地名", "县级类", "地级码" FROM county WHERE "县级码" IS NOT NULL')
    counties = cursor.fetchall()
    for code, name, ctype, parent_code in counties:
        if code:
            G.add_node(code, name=name, level="county", type=ctype)
            if parent_code:
                G.add_edge(code, parent_code, type="BELONGS_TO")

    logger.info("Extracting village/township nodes and relationships...")
    # Get villages and link to counties.
    # For village, area_code typically represents the region code.
    # The parent county code is usually the first 6 digits of the area_code (if area_code is 9+ digits).
    cursor.execute('SELECT area_code, name, layer FROM village WHERE area_code IS NOT NULL')
    villages = cursor.fetchall()
    for code, name, layer in villages:
        if code:
            G.add_node(code, name=name, level="village", type=layer)
            # Assuming area_code is standard Chinese admin code (e.g., 9-12 digits), parent county is first 6 digits
            if len(code) >= 6:
                parent_code = code[:6]
                # Try to link if the county exists
                if parent_code in G:
                    G.add_edge(code, parent_code, type="BELONGS_TO")

    cursor.close()
    conn.close()

    logger.info(f"Knowledge graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G

def export_graph(G, output_file="admin_kg.json"):
    """Export the graph to a JSON node-link format which is highly versatile."""
    if not G:
        logger.error("No graph to export.")
        return

    logger.info(f"Exporting knowledge graph to {output_file}...")
    data = nx.node_link_data(G)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Export complete.")

if __name__ == "__main__":
    kg = build_knowledge_graph()
    if kg:
        export_graph(kg, "admin_knowledge_graph.json")
        export_graph(kg, "admin_knowledge_graph.graphml") # Export to GraphML as well since I can easily do both
        # GraphML requires string keys and string/numeric values, let's clean up nodes before graphml export
        # GraphML is excellent for Gephi visualization.
        try:
            logger.info("Exporting to GraphML format (admin_knowledge_graph.graphml)...")
            nx.write_graphml(kg, "admin_knowledge_graph.graphml", named_key_ids=True)
            logger.info("GraphML export complete.")
        except Exception as e:
            logger.error(f"Failed to export GraphML: {e}")
