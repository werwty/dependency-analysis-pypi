import hashlib
import os
import shutil
import sys

from progress.bar import Bar


def copy_dir(srcd, dstd):
    list_skip = []

    if not os.path.isdir(srcd):
        raise ValueError("%s is not a dir" % srcd)
    elif not os.path.isdir(dstd):
        raise ValueError("%s is not a dir" % dstd)
    else:
        src_flist = os.listdir(srcd)
        total_file = len(src_flist)
        copied_file = 0
        overwrite = 0
        bar = Bar('Copying', max=total_file)

        for srcf in src_flist:
            src_fullpath = os.path.join(srcd, srcf)
            dst_fullpath = os.path.join(dstd, srcf)
            if os.path.isfile(src_fullpath):
                if os.path.exists(dst_fullpath):
                    if os.path.isfile(dst_fullpath):
                        with open(src_fullpath, "rb") as fp:
                            srcf_hash = hashlib.md5(fp.read()).hexdigest()
                        with open(dst_fullpath, "rb") as fp:
                            dstf_hash = hashlib.md5(fp.read()).hexdigest()
                        if srcf_hash == dstf_hash:
                            list_skip.append(("file", srcf, srcf_hash, dstf_hash, srcf_hash == dstf_hash))
                            print("\n\nSkipped: %s => %s (hash same)" % (src_fullpath, dst_fullpath))
                        else:
                            print("\n\n%s => %s (hash diff), overwrite?" % (src_fullpath, dst_fullpath))
                            while (uin := input("[y/N]: ")).lower() not in {"y", "n", ""}:
                                pass
                            if uin.lower() == "y":
                                os.remove(dst_fullpath)
                                shutil.copyfile(src_fullpath, dst_fullpath)
                                copied_file += 1
                                overwrite += 1
                                print("\n\nOverwrite: %s => %s" % (src_fullpath, dst_fullpath))
                            else:
                                list_skip.append(("file", srcf, srcf_hash, dstf_hash, srcf_hash == dstf_hash))
                                print("\n\nSkipped: %s => %s (hash diff)" % (src_fullpath, dst_fullpath))
                    else:
                        list_skip.append(("dir", srcf))
                        print("\n\nSkipped: %s (target is a dir)" % dst_fullpath)

                else:
                    shutil.copyfile(src_fullpath, dst_fullpath)
                    copied_file += 1
            else:
                print("\n\nSkipped: %s (source is a dir)" % src_fullpath)

            bar.next()

        bar.finish()

        print("Summary %s ==> %s, total %d, copied %d" % (srcd, dstd, total_file, copied_file))

    return list_skip


def main():
    src_dir = sys.argv[1]
    dst_dir = sys.argv[2]
    merge_result = sys.argv[3]
    skip_list = []
    for i in range(1, 9):
        skip_list.extend(copy_dir(os.path.join(src_dir, "worker%d" % i, "data"), dst_dir))

    with open(merge_result, "w") as fp:
        for t in skip_list:
            fp.write(str(t))


if __name__ == '__main__':
    main()
