import re
from FHIR_flattener import flatten_fhir, flat_to_string, find_patient

what_to_call_resource = 'entry'

camel_pattern1 = re.compile(r'(.)([A-Z][a-z]+)')
camel_pattern2 = re.compile(r'([a-z0-9])([A-Z])')


def split_camel(text):
    new_text = camel_pattern1.sub(r'\1 \2', text.strip())
    new_text = camel_pattern2.sub(r'\1 \2', new_text.strip())
    return new_text.lower().strip()


date_time_pattern1 = re.compile(r'([0-9]+)-([0-9]+)-([0-9]+)T([0-9:]+)[.+-]')
date_time_pattern2 = re.compile(r'([0-9]+)-([0-9]+)-([0-9]+)')

def any_date_to_str(fhir_date, converter, parent_field=''):
    what = parent_field_to_str(parent_field, 'unknown')
    data_time = date_time_pattern1.findall(fhir_date)[0]
    return [f'This {converter.doc} was {what} on {data_time[1]}/{data_time[2]}/{data_time[0]} at {data_time[3]}.']


def ordinal(n):
    n += 1
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    return str(n) + suffix


def text_to_str(text: str):
    if text.endswith('.'):
        text = text.rstrip('.')
    return text.lower()


def parent_field_to_str(parent_field, default):
    if not parent_field:
        return default
    return split_camel(parent_field)


def ignore_to_str(fhir_value, converter, parent_field=''):
    return []


def combine_fields(parent_field, field):
    if parent_field:
        return f'{parent_field} {field}'
    return split_camel(field)


def default_to_str(fhir_value, converter, parent_field=''):
    if type(fhir_value) is dict:
        flat = flatten_fhir(fhir_value)
        return [f'{parent_field} {flat_to_string(flat)}']
    if type(fhir_value) is list:
        flat = flatten_fhir(fhir_value)
        return [f'{parent_field} {flat_to_string(flat)}']
    return [f'The {parent_field} for this {converter.doc} is {fhir_value}.']


def resource_type_to_str(fhir_value, converter, parent_field=''):
    return [f'The type of information in this {converter.doc} is {split_camel(fhir_value)}.']


def any_code_to_str(fhir_value, converter, parent_field=''):
    output = []
    what = parent_field_to_str(parent_field, 'code')
    if type(fhir_value) is str:
        output.append(f'The {what} for this {converter.doc} is {fhir_value}.')
    elif type(fhir_value) is dict and 'coding' in fhir_value:
        if len(fhir_value['coding']) == 1:
            code_value = fhir_value['coding'][0]
            if 'display' in code_value:
                output.append(f'The {what} for this {converter.doc} is {code_value["display"]}.')
            elif 'code' in code_value:
                output.append(f'The {what} for this {converter.doc} is {code_value["code"]}.')
        else:
            for i, code_value in enumerate(fhir_value['coding']):
                if 'display' in code_value:
                    output.append(f'The {ordinal(i)} {what} for this {converter.doc} is {code_value["display"]}.')
                elif 'code' in code_value:
                    output.append(f'The {ordinal(i)} {what} for this {converter.doc} is {code_value["code"]}.')
    return output


def any_value_quantity_to_str(fhir_value, converter, parent_field=''):
    what = parent_field_to_str(parent_field, 'quantity value')
    return [f'The {what} for this {converter.doc} is {fhir_value["value"]} {fhir_value["unit"]}.']


def any_value_string_to_str(fhir_value, converter, parent_field=''):
    what = parent_field_to_str(parent_field, 'value')
    return [f'The {what} for this {converter.doc} is {fhir_value}']


def any_value_codeable_concept_to_str(fhir_value, converter, parent_field=''):
    what = parent_field_to_str(parent_field, 'value or result')
    if 'display' in fhir_value["coding"][0]:
        return [f'The {what} for this {converter.doc} is {fhir_value["coding"][0]["display"]}.']
    if 'code' in fhir_value["coding"][0]:
        return [f'The {what} for this {converter.doc} is {fhir_value["coding"][0]["code"]}.']
    return []


def any_status_to_str(fhir_value, converter, parent_field=''):
    what = parent_field_to_str(parent_field, 'status')
    return [f'The {what} for this {converter.doc} is {fhir_value}.']


def any_category_to_str(fhir_value, converter, parent_field=''):
    output = []
    what = parent_field_to_str(parent_field, 'category')
    if type(fhir_value) is list:
        if len(fhir_value) == 1:
            category = fhir_value[0]
            if type(category) is dict and 'coding' in category:
                for code_value in category['coding']:
                    if 'display' in code_value:
                        output.append(f'The {what} of this {converter.doc} is {code_value["display"]}.')
                    elif 'code' in code_value:
                        output.append(f'The {what} of this {converter.doc} is {code_value["code"]}.')
            else:
                output.append(f'The {what} of this {converter.doc} is {category}.')
        else:
            for i, category in enumerate(fhir_value):
                if type(category) is dict and 'coding' in category:
                    for code_value in category['coding']:
                        if 'display' in code_value:
                            output.append(
                                f'The {ordinal(i)} {what} of this {converter.doc} is {code_value["display"]}.')
                        elif 'code' in code_value:
                            output.append(f'The {ordinal(i)} {what} of this {converter.doc} is {code_value["code"]}.')
                else:
                    output.append(f'The {ordinal(i)} {what} of this {converter.doc} is {category}.')
    elif type(fhir_value) is dict and 'coding' in fhir_value:
        for code_value in fhir_value['coding']:
            for code_value in fhir_value['coding']:
                if 'display' in code_value:
                    output.append(f'The {what} of this {converter.doc} is {code_value["display"]}.')
                elif 'code' in code_value:
                    output.append(f'The {what} of this {converter.doc} is {code_value["code"]}.')
    else:
        output.append(f'The {what} of this {converter.doc} is {fhir_value}.')

    return output


def any_components_to_str(fhir_value, converter, parent_field=''):
    output = []
    what = parent_field_to_str(parent_field, 'component')
    output.append(f'This {converter.doc} contains {len(fhir_value)} {what}s.')
    for i, component in enumerate(fhir_value):
        output += converter.convert(component, parent_field=f"{ordinal(i)} {what}'s")
    return output


reaction_to_str_dict = {
    'substance': any_code_to_str,
    'manifestation': any_category_to_str,
    'severity': any_code_to_str
}


def any_reaction_to_str(fhir_value, converter, parent_field=''):
    output = []
    what = parent_field_to_str(parent_field, 'reaction')
    if type(fhir_value) is list:
        for i, reaction in enumerate(fhir_value):
            for field, value in reaction.items():
                if field in reaction_to_str_dict:
                    output += reaction_to_str_dict[field](value, converter, parent_field=f'{ordinal(i)} {what} {field}')
                else:
                    output += default_to_str(value, converter, parent_field=f'{ordinal(i)} {what} {field}')
    return output


def any_dosage_instruction_to_str(fhir_value, converter, parent_field=''):
    output = []
    what = parent_field_to_str(parent_field, 'dosage instruction')
    if len(fhir_value) == 1:
        if 'text' in fhir_value[0]:
            output.append(f'The {what} for this {converter.doc} is {text_to_str(fhir_value[0]["text"])}.')
    else:
        for dosage in fhir_value:
            if 'sequence' in dosage and 'text' in dosage:
                output.append(
                    f'The {ordinal(dosage["sequence"])} {what} for this {converter.doc} is {text_to_str(fhir_value["text"])}.')
    return output


def any_insurance_to_str(fhir_value, converter, parent_field=''):
    output = []
    what = parent_field_to_str(parent_field, 'insurance')
    if len(fhir_value) == 1:
        if 'coverage' in fhir_value[0] and 'display' in fhir_value[0]['coverage']:
            output.append(f'The {what} for this {converter.doc} is {fhir_value[0]["coverage"]["display"]}.')
    else:
        for dosage in fhir_value:
            if 'sequence' in dosage and 'coverage' in dosage and 'display' in dosage['coverage']:
                output.append(
                    f'The {ordinal(dosage["sequence"])} {what} for this {converter.doc} is {dosage["coverage"]["display"]}.')
    return output


def any_claim_item_to_str(fhir_value, converter, parent_field=''):
    output = []
    what = parent_field_to_str(parent_field, 'item')
    if len(fhir_value) == 1:
        if 'productOrService' in fhir_value[0]:
            output += any_code_to_str(fhir_value[0]['productOrService'], converter, parent_field=what)
    else:
        for item in fhir_value:
            if 'sequence' in item and 'productOrService' in item:
                output += any_code_to_str(fhir_value[0]['productOrService'], converter,
                                          parent_field=f'{ordinal(item["sequence"])} {what} ')
    return output


def any_reference_to_str(fhir_value, converter, parent_field=''):
    # what = parent_field_to_str(parent_field, 'reference')
    # if 'display' in fhir_value:
    #     return [f'The {what} for this {converter.doc} is {fhir_value["display"]}.']
    # if 'reference' in fhir_value:
    #     return [f'The {what} for this {converter.doc} is {fhir_value["reference"]}.']
    return []


def any_class_to_str(fhir_value, converter, parent_field=''):
    what = parent_field_to_str(parent_field, 'class')
    if 'display' in fhir_value:
        return [f'The {what} for this {converter.doc} is {fhir_value["display"]}.']
    if 'code' in fhir_value:
        return [f'The {what} for this {converter.doc} is {fhir_value["code"]}.']
    return []


def any_simple_money_to_str(fhir_value, converter, parent_field=''):
    what = parent_field_to_str(parent_field, 'money')
    if 'value' in fhir_value and 'currency' in fhir_value:
        return [f'The {what} for this {converter.doc} is {fhir_value["value"]} {fhir_value["currency"]}.']
    if 'value' in fhir_value:
        return [f'The {what} for this {converter.doc} is {fhir_value["value"]}.']
    return []


def any_contained_to_str(fhir_value, converter, parent_field=''):
    output = []
    for i, resource in enumerate(fhir_value):
        resource_type = resource['resourceType']
        if resource_type in resource_conveter_dict:
            output += resource_conveter_dict[resource_type](resource, doc=f'{ordinal(i)} sub{converter.doc}').convert()
        else:
            output += GenericConverter(resource, doc=f'{ordinal(i)} sub{converter.doc}').convert()
    return output


generic_field_to_str_dict = {
    'resourceType': resource_type_to_str,
    'id': ignore_to_str,
    'identifier': ignore_to_str,
    'extension': ignore_to_str,
    'meta': ignore_to_str,
    'subject': ignore_to_str,
    'patient': ignore_to_str,
    'text': ignore_to_str,
    'code': any_code_to_str,
    'role': any_code_to_str,
    'maritalStatus': any_code_to_str,
    'language': any_code_to_str,
    'valueQuantity': any_value_quantity_to_str,
    'valueString': any_value_string_to_str,
    'valueCodeableConcept': any_value_codeable_concept_to_str,
    'status': any_status_to_str,
    'effectiveDateTime': any_date_to_str,
    'recordedDate': any_date_to_str,
    'issued': any_date_to_str,
    'start': any_date_to_str,
    'end': any_date_to_str,
    'authoredOn': any_date_to_str,
    'onsetDateTime': any_date_to_str,
    'abatementDateTime': any_date_to_str,
    'occurrenceDateTime': any_date_to_str,
    'created': any_date_to_str,
    'category': any_category_to_str,
    'clinicalStatus': any_code_to_str,
    'verificationStatus': any_code_to_str,
    'reaction': any_reaction_to_str,
    'component': any_components_to_str,
    'medicationCodeableConcept': any_code_to_str,
    'requester': any_reference_to_str,
    'dosageInstruction': any_dosage_instruction_to_str,
    'location': any_reference_to_str,
    'vaccineCode': any_code_to_str,
    'class': any_class_to_str,
    'type': any_category_to_str,
    'individual': any_reference_to_str,
    'serviceProvider': any_reference_to_str,
    'provider': any_reference_to_str,
    'performer': any_reference_to_str,
    'reference': any_reference_to_str,
    'priority': any_code_to_str,
    'insurance': any_insurance_to_str,
    'item': any_claim_item_to_str,
    'contained': any_contained_to_str
}

claim_field_to_str_dict = generic_field_to_str_dict.copy()
claim_field_to_str_dict['total'] = any_simple_money_to_str

explanation_of_benefit_field_to_str_dict = generic_field_to_str_dict.copy()
# explanation_of_benefit_field_to_str_dict['total'] = lambda fhir_value,parent_field='',doc='': ['TOTAL HERE!']
explanation_of_benefit_field_to_str_dict['amount'] = any_simple_money_to_str


def ignore_converter(resource):
    return None


class GenericConverter:
    def __init__(self, resource, doc=None, field_to_str_dict=None):
        self.resource = resource
        if field_to_str_dict is None:
            self.field_to_str_dict = generic_field_to_str_dict
        else:
            self.field_to_str_dict = field_to_str_dict
        if doc is None:
            self.doc = what_to_call_resource
        else:
            self.doc = doc

    def convert(self, resource=None, parent_field='', converter=None):
        if resource is None:
            resource = self.resource
        if converter is None:
            converter = self
        output = []
        if type(resource) is dict:
            for field, value in resource.items():
                if field == 'resourceType':
                    output += resource_type_to_str(value, converter)
                    converter.doc = split_camel(value)
                elif field in self.field_to_str_dict:
                    output += self.field_to_str_dict[field](value, converter,
                                                            parent_field=combine_fields(parent_field, field))
                elif type(value) is dict:
                    output += converter.convert(value, parent_field=combine_fields(parent_field, field))
                elif type(value) is list:
                    if len(value) == 1:
                        output += converter.convert(value[0], parent_field=combine_fields(parent_field, field))
                    else:
                        for i, item in enumerate(value):
                            output += converter.convert(item, parent_field=combine_fields(parent_field, combine_fields(field, i)))
                else:
                    output += default_to_str(value, converter, parent_field=combine_fields(parent_field, field))
        else:
            output += default_to_str(resource, converter, parent_field=parent_field)
        return output


class IgnoreConverter(GenericConverter):
    def __init__(self, resource, doc=None, field_to_str_dict=None):
        super().__init__(resource, doc, field_to_str_dict)

    def convert(self, resource=None, parent_field='', converter=None):
        return None


resource_conveter_dict = {
    'DocumentReference': lambda resource, doc=None: IgnoreConverter(resource, doc=doc),
    'DiagnosticReport': lambda resource, doc=None: IgnoreConverter(resource, doc=doc),
    'Claim': lambda resource, doc=None: GenericConverter(resource, doc=doc, field_to_str_dict=claim_field_to_str_dict),
    'ExplanationOfBenefit': lambda resource, doc=None: GenericConverter(resource, doc=doc,
                                                                        field_to_str_dict=explanation_of_benefit_field_to_str_dict)
}


def date_of_birth_to_str(date):
    data_time = date_time_pattern2.findall(date)[0]
    return f'{data_time[1]}/{data_time[2]}/{data_time[0]}'


def patient_to_str(patient, doc=what_to_call_resource):
    return f'This {doc} is for patient {patient["PatientFirstName"]} {patient["PatientLastName"]}. Who was born on {date_of_birth_to_str(patient["dateOfBirth"])} and whose gender is {patient["gender"]}.'


def FHIR_to_string(resource):
    resource_type = resource['resourceType']
    if resource_type in resource_conveter_dict:
        return resource_conveter_dict[resource_type](resource).convert()
    return GenericConverter(resource).convert()


def FHIR_bundle_to_strings(bundle):
    patient, patient_name = find_patient(bundle)
    patient_str = patient_to_str(patient)
    output = []
    for entry in bundle['entry']:
        fhir_str = FHIR_to_string(entry['resource'])
        if fhir_str is not None:
            fhir_str = ' '.join(fhir_str)
            output.append(f'{patient_str}\n{fhir_str}')
    return output, patient_name
