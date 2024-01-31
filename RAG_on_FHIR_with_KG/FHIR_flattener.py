import re

camel_pattern1 = re.compile(r'(.)([A-Z][a-z]+)')
camel_pattern2 = re.compile(r'([a-z0-9])([A-Z])')


def split_camel(text):
    new_text = camel_pattern1.sub(r'\1 \2', text.strip())
    new_text = camel_pattern2.sub(r'\1 \2', new_text.strip())
    return new_text.lower().strip()

def handle_special_attributes(attrib_name, value):
    if attrib_name == 'resource Type':
        return split_camel(value)
    return value


def flatten_fhir(nested_json):
    out = {}

    def flatten(json_to_flatten, name=''):
        if type(json_to_flatten) is dict:
            for sub_attribute in json_to_flatten:
                flatten(json_to_flatten[sub_attribute], name + split_camel(sub_attribute) + ' ')
        elif type(json_to_flatten) is list:
            for i, sub_json in enumerate(json_to_flatten):
                flatten(sub_json, name + str(i) + ' ')
        else:
            attrib_name = name[:-1]
            out[attrib_name] = handle_special_attributes(attrib_name, json_to_flatten)

    flatten(nested_json)
    return out


def filter_for_patient(entry):
    return entry['resource']['resourceType'] == "Patient"


def find_patient(bundle):
    patients = list(filter(filter_for_patient, bundle['entry']))
    if len(patients) < 1:
        raise Exception('No Patient found in bundle!')
    else:
        patient = patients[0]['resource']

        patient_id = patient['id']
        first_name = patient['name'][0]['given'][0]
        last_name = patient['name'][0]['family']
        dateOfBirth = patient['birthDate']
        gender = patient['gender']

        return {
            'PatientFirstName': first_name,
            'PatientLastName': last_name,
            'PatientID': patient_id,
            'dateOfBirth': dateOfBirth,
            'gender': gender
        }, f'{first_name} {last_name}'


def flat_to_string(flat_entry):
    output = ''

    for attrib in flat_entry:
        output += f'{attrib} is {flat_entry[attrib]}. '

    return output


def FHIR_flatten_bundle(bundle):
    patient, patient_name = find_patient(bundle)
    flat_patient = flatten_fhir(patient)
    output = []
    for entry in bundle['entry']:
        flat_entry = flatten_fhir(entry['resource'])
        output.append(f'{flat_to_string(flat_patient)}\n{flat_to_string(flat_entry)}')
    return output, patient_name
