# Date: 2019-12-26
# Author: Devon Chen

"""
This program hides an image (secret) inside another image (camul).
The generated image (hidden) will be four times larger than camul.
"""

import argparse
import sys
import os
from PIL import Image


def get_2bit_groups(value):
    """
    value: a valid value for rgb (0 ~ 255)
    return: a four-element tuple made up of the four groups of bits

    Example: value = 0b 10 11 01 00
    get_2bit_groups(value) returns (0b 10, 0b 11, 0b 01, 0b 00)
    """
    return reversed([(value & (0b11 << (2 * i))) >> (2 * i) for i in range(4)])


def truncate_rightmost_2bits(value):
    return value >> 2 << 2


def merge_pixel_value(camul_value, secret_value):
    values = get_2bit_groups(secret_value)
    truncated = truncate_rightmost_2bits(camul_value)
    return [truncated + value for value in values]


def extract_pixel_value(camul_values):
    values = [cv % (1 << 2) for cv in camul_values]
    secret_value = values[0]
    for value in values[1:]:
        secret_value = secret_value << 2
        secret_value += value
    return secret_value


def hide_image(camul, secret):
    camul_data = Image.open(camul)
    secret_data = Image.open(secret)

    cxs, cys = camul_data.size
    sxs, sys = secret_data.size

    data_xs = min(cxs, sxs)
    data_ys = min(cys, sys)
    data = Image.new('RGB', (2*data_xs, 2*data_ys))

    for i in range(data_xs):
        for j in range(data_ys):
            p = camul_data.getpixel((i, j))
            q = secret_data.getpixel((i, j))

            red_values = merge_pixel_value(p[0], q[0])
            green_values = merge_pixel_value(p[1], q[1])
            blue_values = merge_pixel_value(p[2], q[2])
            
            data.putpixel((2*i, 2*j), (red_values[0], green_values[0], blue_values[0]))
            data.putpixel((2*i+1, 2*j), (red_values[1], green_values[1], blue_values[1]))
            data.putpixel((2*i, 2*j+1), (red_values[2], green_values[2], blue_values[2]))
            data.putpixel((2*i+1, 2*j+1), (red_values[3], green_values[3], blue_values[3]))

    return data


def extract_image(camul):
    camul_data = Image.open(camul)
    cxs, cys = camul_data.size

    data_xs = cxs // 2
    data_ys = cys // 2
    data = Image.new('RGB', (data_xs, data_ys))

    for i in range(data_xs):
        for j in range(data_ys):
            p1 = camul_data.getpixel((2*i, 2*j))
            p2 = camul_data.getpixel((2*i+1, 2*j))
            p3 = camul_data.getpixel((2*i, 2*j+1))
            p4 = camul_data.getpixel((2*i+1, 2*j+1))

            q_red = extract_pixel_value([p1[0], p2[0], p3[0], p4[0]])
            q_green = extract_pixel_value([p1[1], p2[1], p3[1], p4[1]])
            q_blue = extract_pixel_value([p1[2], p2[2], p3[2], p4[2]])

            data.putpixel((i, j), (q_red, q_green, q_blue))

    return data


def main():
    parser = argparse.ArgumentParser(description='Hide or extract image inside/from another')
    parser.add_argument('-m', '--method', dest='method', nargs=1, required=True, metavar='[hide|extract]')
    parser.add_argument('-c', '--camul', dest='camul', nargs=1, required=True)
    parser.add_argument('-s', '--secret', dest='secret', nargs=1)
    parser.add_argument('-o', '--output', dest='output', nargs='?')
    args = parser.parse_args()

    args.method = args.method[0].lower()
    args.camul = args.camul[0]
    if args.method == 'hide':
        args.secret = args.secret[0]

    if args.method != 'hide' and args.method != 'extract':
        sys.stderr.write("Error: invalid method")
        sys.exit(1)

    if args.method == 'hide' and args.secret is None:
        sys.stderr.write("Error: Method hide requires secret to be provided")
        sys.exit(1)

    if (not os.path.exists(args.camul)) or (not os.path.isfile(args.camul)):
        sys.stderr.write(f"Error: {args.camul} doesn't exist or is not a file")
        sys.exit(1)

    if args.method == 'hide':
        if (not os.path.exists(args.secret)) or (not os.path.isfile(args.secret)):
            sys.stderr.write(f"Error: {args.secret} doesn't exist or is not a file")
            sys.exit(1)

    if args.output is not None and os.path.exists(args.output):
        sys.stderr.write(f"Error: {args.output} already exists")
        sys.exit(1)


    if args.method == 'hide':
        if args.output is None:
            args.output = 'hidden' + os.path.splitext(args.camul)[-1]
        hide_image(args.camul, args.secret).save(args.output)
    else:
        if args.output is None:
            args.output = 'extracted' + os.path.splitext(args.camul)[-1]
        extract_image(args.camul).save(args.output)

    print(f"{args.output} generated")


if __name__ == '__main__':

    main()

