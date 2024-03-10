import sys
import os

def copy_to_folder(file_path, folder_path):
    with open(file_path, 'rb') as file:
        data = file.read()
    copy_to = folder_path + '/' +file_path.split('/')[-1]
    with open(copy_to, 'wb') as file:
        file.write(data)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        base_folder = "/Users/prithvirajchaudhuri/Downloads/"+sys.argv[2]
        base_folder = base_folder.strip().replace(':','-').replace('?','')
        os.makedirs(base_folder, exist_ok=True)
        copy_to_folder(sys.argv[1], base_folder)
        print(sys.argv[2].strip().replace(':','-'))
    else:
        print("Invalid arguments. Exiting...")
        exit(1)