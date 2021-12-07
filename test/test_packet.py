from packet import Packet


def check_layer(packet, name, size, letter):
    layer = packet.get_layer(name)
    assert layer.attributes == {'size': size}
    assert len(layer.data) == size
    assert layer.data == letter * size
    assert layer.tail is None


def test_layers():
    first_layers_size = 10
    second_layer_size = 20
    third_layer_size = 30

    packet = Packet(b'a' * first_layers_size + b'b' * second_layer_size + b'c' * third_layer_size)
    packet.add_layer('first', {'size': first_layers_size}, first_layers_size)
    packet.add_layer('second', {'size': second_layer_size}, second_layer_size)
    assert packet.current_packet == b'c' * third_layer_size
    packet.add_layer('third', {'size': third_layer_size}, third_layer_size)

    check_layer(packet, 'first', first_layers_size, b'a')
    check_layer(packet, 'second', second_layer_size, b'b')
    check_layer(packet, 'third', third_layer_size, b'c')


def test_tail():
    head_size = 5
    middle_size = 10
    tail_size = 15

    packet = Packet(b'a' * head_size + b'b' * middle_size + b'c' * tail_size)
    packet.add_layer('layer', {}, head_size, tail_size)
    assert packet.current_packet == b'b' * middle_size

    layer = packet.get_layer('layer')
    assert layer.data == b'a' * head_size
    assert layer.tail == b'c' * tail_size
