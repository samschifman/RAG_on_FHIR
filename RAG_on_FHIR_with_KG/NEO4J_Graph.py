import time
from neo4j import GraphDatabase


class timer:
    def __init__(self):
        self._start = time.time()
        self._end = None
        self._runtime = None

    def end(self):
        self._end = time.time()
        self._runtime = float(str(time.time() - self._start)[:5])
        return self._runtime


class Graph:
    def __init__(self, url, username, password):
        self._url = url
        self._username = username
        self._password = password

    # Helper function that runs cypher transaction on local database
    def cypher_transaction(self, cypher):
        driver = GraphDatabase.driver(self._url, auth=(self._username, self._password))
        values = []
        with driver.session() as session:
            res = session.run(cypher)
            for record in res:
                values.append(record.values())
        driver.close()
        return values

    # Helper function wrapped around cypher_transaction() for timing
    def query(self, cypher):
        time = timer()
        result = self.cypher_transaction(cypher)
        runtime = time.end()
        return result, runtime

    # Get type and number of each FHIR resource in the database
    def resource_metrics(self):
        cypher = f'''
            MATCH (r:resource) 
            WITH DISTINCT(r.resource_type) AS resource_types
                ORDER BY resource_types
            UNWIND resource_types as resource_type
            MATCH (r:resource)
            WHERE r.resource_type = resource_type
            WITH resource_type, COUNT(r) as resource_count
            RETURN resource_type, resource_count
                ORDER BY resource_count
        '''

        resource_count, runtime = self.query(cypher)
        return resource_count


    # Standard metrics for counting nodes and relationships
    def database_metrics(self):
        node_count = 0
        relationship_count = 0

        cypher = f'''
            MATCH (n) 
            WITH COUNT(n) as node_count
            MATCH ()-[r]->()
            WITH node_count, COUNT(r) as relationship_count
            RETURN node_count, relationship_count
        '''

        count_result, runtime = self.query(cypher)
        if (len(count_result) != 0):
            node_count = count_result[0][0]
            relationship_count = count_result[0][1]

        return node_count, relationship_count

    # Deletes all nodes and their relationships in database
    def wipe_database(self):
        node_count, relationship_count = self.database_metrics()

        cypher = f'''
            MATCH (n) DETACH DELETE n
        '''

        delete_result, runtime = self.query(cypher)
        return 'Deleted {} nodes and {} relationships in {} seconds'.format( node_count, relationship_count, runtime )