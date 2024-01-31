import re
from FHIR_to_string import FHIR_to_string

camel_pattern1 = re.compile(r'(.)([A-Z][a-z]+)')
camel_pattern2 = re.compile(r'([a-z0-9])([A-Z])')

def split_camel(text):
    new_text = camel_pattern1.sub(r'\1_\2', text.strip())
    new_text = camel_pattern2.sub(r'\1_\2', new_text.strip())
    return new_text.lower().strip()

def flatten_fhir(nested_json):
    out = {}

    def flatten(json_to_flatten, name=''):
        if name == 'text_':
            return
        elif type(json_to_flatten) is dict:
            for sub_attribute in json_to_flatten:
                flatten(json_to_flatten[sub_attribute], name + split_camel(sub_attribute) + '_')
        elif type(json_to_flatten) is list:
            for i, sub_json in enumerate(json_to_flatten):
                flatten(sub_json, name + str(i) + '_')
        else:
            attrib_name = name[:-1]
            out[attrib_name] = json_to_flatten

    flatten(nested_json)
    return out

def flat_fhir_to_json_str(flat_fhir, name, fhir_str):
    output = '{' + f'name: "{name}",'


    if fhir_str is not None:
        fhir_str = ' '.join(fhir_str)
        output += f'text: "{fhir_str}",'

    for attrib in flat_fhir:
        output += f'{attrib}: "{flat_fhir[attrib]}",'

    output = output[:-1]
    output += '}'

    return output

def id_to_property_str(id):
    return "{id: '" + id + "'}"

def npi_to_property_str(id):
    return "{identifier_0_value: '" + id + "', identifier_0_system: 'http://hl7.org/fhir/sid/us-npi'}"

def extract_id(value: str):
    if value.startswith('urn:uuid:'):
        return id_to_property_str(value[9:])
    elif value.startswith('Location'):
        index = value.index('|')
        return id_to_property_str(value[index+1:])
    elif value.startswith('Organization'):
        index = value.index('|')
        return id_to_property_str(value[index+1:])
    elif value.startswith('Practitioner'):
        index = value.index('|')
        return npi_to_property_str(value[index+1:])
    elif value[0:1] == '#':
        return None
    else:
        print(f'Unrecognized reference: {value}')
        return None

date_containing_fields=[
    'effectiveDateTime', 'recordedDate', 'issued',
    'start', 'end', 'authoredOn', 'onsetDateTime',
    'abatementDateTime', 'occurrenceDateTime', 'created'
]
date_pattern = re.compile(r'([0-9]+)-([0-9]+)-([0-9]+)')
def extract_date(value: str):
    data_parts = date_pattern.findall(value)[0]
    return f'{data_parts[1]}/{data_parts[2]}/{data_parts[0]}'

def resource_to_edges(resource):
    resource_type = resource['resourceType']
    resource_id = resource['id']

    references = []
    dates = []
    def search(json_to_flatten, name=''):
        if name == 'text_':
            return
        elif type(json_to_flatten) is dict:
            for sub_attribute in json_to_flatten:
                if sub_attribute == 'reference':
                    relation = name[:-1]
                    reference_id_str = extract_id(json_to_flatten[sub_attribute])
                    if reference_id_str is not None:
                        cypher = f'''
                            MATCH (n1 {id_to_property_str(resource_id)}), (n2 {reference_id_str})
                            CREATE (n1)-[:{relation}]->(n2)
                        '''
                        references.append(cypher)
                elif resource_type == 'PractitionerRole' and sub_attribute == 'practitioner':
                    relation = 'practitioner'
                    reference_id_str = npi_to_property_str(json_to_flatten[sub_attribute]['identifier']['value'])
                    if reference_id_str is not None:
                        cypher = f'''
                            MATCH (n1 {id_to_property_str(resource_id)}), (n2 {reference_id_str})
                            CREATE (n1)-[:{relation}]->(n2)
                        '''
                        references.append(cypher)
                elif resource_type == 'PractitionerRole' and sub_attribute == 'organization':
                    relation = 'organization'
                    reference_id_str = id_to_property_str(json_to_flatten[sub_attribute]['identifier']['value'])
                    if reference_id_str is not None:
                        cypher = f'''
                            MATCH (n1 {id_to_property_str(resource_id)}), (n2 {reference_id_str})
                            CREATE (n1)-[:{relation}]->(n2)
                        '''
                        references.append(cypher)
                elif sub_attribute in date_containing_fields:
                    relation = name + split_camel(sub_attribute)
                    date_str = extract_date(json_to_flatten[sub_attribute])
                    if date_str is not None:
                        dates.append(date_str)
                        cypher = f'''
                            MATCH (n1 {id_to_property_str(resource_id)}), (n2 {id_to_property_str(date_str)})
                            CREATE (n1)-[:{relation}]->(n2)
                        '''
                        references.append(cypher)
                else:
                    search(json_to_flatten[sub_attribute], name + split_camel(sub_attribute) + '_')
        elif type(json_to_flatten) is list:
            for i, sub_json in enumerate(json_to_flatten):
                search(sub_json, name + str(i) + '_')

    search(resource)
    return references, dates

def resource_to_node(resource):
    resource_type = resource['resourceType']
    flat_resource = flat_fhir_to_json_str(flatten_fhir(resource), resource_name(resource), FHIR_to_string(resource))
    return f'CREATE (:{resource_type}:resource {flat_resource})'


def resource_name(resource):
    rt = resource['resourceType']
    if rt == 'Patient':
        return f'{resource["name"][0]["given"][0]} {resource["name"][0]["family"]}'
    else:
        return rt
