import argparse
import json


# def parse_labelling(diff_processes):
#     with open(diff_processes, 'r') as cfile:
#         data = json.load(cfile)
#         list_p = []
#         if "total_commands" in data:
#             tmp_write_dic = data["total_commands"]
#             for key, file_ in tmp_write_dic.items():
#                 list_p.append(file_['id'])

#         if "total_commands_multi" in data:
#             multi_write_t = data["total_commands_multi"]
#             for key, file_ in multi_write_t.items():
#                 list_p.append(file_['id'])
#     return list_p


def merge_processes(input1_, input2_, output_):
    cfile1 = open(input1_, 'r')
    data1_ = json.load(cfile1)
    cfile2 = open(input2_, 'r')
    data2_ = json.load(cfile2)
    #data1_.update(data2_)
    data1_["total_commands"].update(data2_["total_commands"])
    data1_["total_commands_multi"].update(data2_["total_commands_multi"])
    with open(output_, 'w') as wfile:
        json.dump(data1_, wfile, indent=4, sort_keys=True)
    multi_write_t = data1_["total_commands_multi"]
    tmp_write_dic = data1_["total_commands"]
    list_p = []
    for lst in [multi_write_t, tmp_write_dic]:
        for key, file_ in lst.items():
            list_p.append(file_['id'])
    return list_p


def main():
    parser = argparse.ArgumentParser(description="Computes a \
                                     checkerboard of the two images.")
    parser.add_argument("input1_json")
    parser.add_argument("input2_json")
    parser.add_argument("output_json")
    args = parser.parse_args()
    input1_ = args.input1_json
    input2_ = args.input2_json
    output_ = args.output_json
    # total_proc_diff = parse_labelling(input1_)
    # print(total_proc_diff)
    # total_proc_diff = parse_labelling(input2_)
    # print(total_proc_diff)
    mgd = merge_processes(input1_, input2_, output_)
    print("The merged processes: {}".format(mgd))
    # if sorted(mgd) != sorted(total_proc_diff):
    #     print("This is different")

if __name__ == '__main__':
    main()
