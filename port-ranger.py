import yaml
import click

def extract_ports_and_generate_names_for_service(data, identifier, start_port, end_port, protocols):
    """
    Process the Service YAML file, add missing ports for the given range and protocol(s),
    and generate unique names for each port entry.
    """
    ports = data.get('spec', {}).get('ports', [])
    existing_ports = {(port['port'], port['protocol']): port for port in ports}
    index = 1

    for port in range(start_port, end_port + 1):
        for protocol in protocols:
            if (port, protocol) not in existing_ports:
                port_entry = {
                    'protocol': protocol,
                    'port': port,
                    'targetPort': port,
                    'name': f"{identifier}-{protocol.lower()}-{index}"
                }
                ports.append(port_entry)
                index += 1
                existing_ports[(port, protocol)] = port_entry

    data['spec']['ports'] = ports
    return data

def extract_ports_and_generate_names_for_udproute(data, identifier, start_port, end_port, chunk_size):
    """
    Process the UDPRoute YAML file, add missing backendRefs for the given port range,
    and ensure proper naming for each backendRef entry. Create multiple UDPRoute objects if chunk size is specified.
    """
    udp_routes = []
    all_ports = range(start_port, end_port + 1)
    chunks = [all_ports[i:i + chunk_size] for i in range(0, len(all_ports), chunk_size)]

    k8s_namespace = data.get('metadata', {}).get('namespace', 'default')

    for chunk_index, chunk in enumerate(chunks):
        rules = [{'backendRefs': []}]
        backend_refs = rules[0].get('backendRefs', [])

        for port in chunk:
            backend_ref = {
                'name': f"{identifier}-service",
                'namespace': k8s_namespace,
                'port': port,
                'kind': 'Service'
            }
            backend_refs.append(backend_ref)

        rules[0]['backendRefs'] = backend_refs
        udp_route = {
            'apiVersion': 'gateway.networking.k8s.io/v1alpha2',
            'kind': 'UDPRoute',
            'metadata': {
                'name': f"{identifier}-udp-route-{chunk_index + 1}",
                'namespace': k8s_namespace
            },
            'spec': {
                'parentRefs': [
                    {
                        'name': 'envoy-gateway',  # Replace with the actual gateway name
                        'namespace': k8s_namespace
                    }
                ],
                'rules': rules
            }
        }
        udp_routes.append(udp_route)

    return udp_routes

@click.command()
@click.argument('yaml_file', type=click.Path(exists=True))
@click.argument('identifier', type=str)
@click.argument('start_port', type=int)
@click.argument('end_port', type=int)
@click.argument('protocols', type=click.Choice(['TCP', 'UDP', 'both'], case_sensitive=False))
@click.argument('output_yaml', type=click.Path())
@click.option('--chunk-size', type=int, default=0, help="Chunk size for creating multiple UDPRoute objects.")
def generate_service_names(yaml_file, identifier, start_port, end_port, protocols, output_yaml, chunk_size):
    """
    Process the YAML file to add ports/backendRefs and generate unique names for a Kubernetes Service or UDPRoute.
    usage:
    ```
    python3 port-ranger.py ./input.yaml unique-identifier 49152 51000 both ./output.yaml --chunk-size 100
    ```
    """
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)

    kind = data.get('kind', '').lower()

    if kind == 'service':
        if protocols == 'both':
            protocols = ['TCP', 'UDP']
        else:
            protocols = [protocols]
        modified_yaml = extract_ports_and_generate_names_for_service(data, identifier, start_port, end_port, protocols)

        with open(output_yaml, 'w') as output_file:
            yaml.dump(modified_yaml, output_file, default_flow_style=False)

    elif kind == 'udproute':
        if protocols != 'UDP' and protocols != 'both':
            raise click.ClickException("UDPRoute only supports UDP protocol.")

        udp_routes = extract_ports_and_generate_names_for_udproute(data, identifier, start_port, end_port, chunk_size)

        with open(output_yaml, 'w') as output_file:
            yaml.dump_all(udp_routes, output_file, default_flow_style=False)

    else:
        raise click.ClickException("Unsupported kind in YAML file. Supported kinds are: Service, UDPRoute.")

    click.echo(f"Modified YAML has been saved to {output_yaml}")

if __name__ == '__main__':
    generate_service_names()
