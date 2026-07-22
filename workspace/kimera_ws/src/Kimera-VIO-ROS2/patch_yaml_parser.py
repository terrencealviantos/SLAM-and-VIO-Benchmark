import os

fn_yaml = './src/MIT-SPARK/Kimera-VIO/include/kimera-vio/utils/YamlParser.h'
if os.path.exists(fn_yaml):
    print("Found YamlParser.h, applying patch...")
    c = open(fn_yaml).read()
    
    # Swap member order to prevent offset corruption from FileStorage size mismatch
    c = c.replace(
        '  cv::FileStorage fs_;\n  std::string filepath_;',
        '  std::string filepath_;\n  cv::FileStorage fs_;'
    )
    
    # Update constructor to initialize filepath_ first
    c = c.replace(
        'YamlParser(const std::string& filepath) : fs_(), filepath_(filepath) {\n    openFile(filepath, &fs_);\n  }',
        'YamlParser(const std::string& filepath) : filepath_(filepath), fs_() {\n    openFile(filepath_, &fs_);\n  }'
    )
    
    # Add debug statements
    c = c.replace(
        'const cv::FileNode& file_handle = fs_[id];',
        'const cv::FileNode& file_handle = fs_[id]; std::cout << "[YamlParser] getYamlParam: " << id << " in file: " << filepath_ << std::endl;'
    )
    
    open(fn_yaml, 'w').write(c)
    print("YamlParser.h patch applied successfully.")
else:
    print("YamlParser.h not found at " + fn_yaml)

fn_cpp = './src/MIT-SPARK/Kimera-VIO/src/frontend/feature-detector/FeatureDetectorParams.cpp'
if os.path.exists(fn_cpp):
    print("Found FeatureDetectorParams.cpp, applying patch...")
    c = open(fn_cpp).read()
    
    # Fix the missing return statement in FeatureDetectorParams::parseYAML (Undefined Behavior)
    target = '  // FAST specific params\n  yaml_parser.getYamlParam("fast_thresh", &fast_thresh_);\n}'
    replacement = '  // FAST specific params\n  yaml_parser.getYamlParam("fast_thresh", &fast_thresh_);\n  return true;\n}'
    
    if target in c:
        c = c.replace(target, replacement)
        open(fn_cpp, 'w').write(c)
        print("FeatureDetectorParams.cpp patch applied successfully.")
    else:
        # Try with different newlines or formatting
        target_alt = 'yaml_parser.getYamlParam("fast_thresh", &fast_thresh_);\n}'
        replacement_alt = 'yaml_parser.getYamlParam("fast_thresh", &fast_thresh_);\n  return true;\n}'
        if target_alt in c:
            c = c.replace(target_alt, replacement_alt)
            open(fn_cpp, 'w').write(c)
            print("FeatureDetectorParams.cpp alt patch applied successfully.")
        else:
            print("Could not find patch target in FeatureDetectorParams.cpp")
else:
    print("FeatureDetectorParams.cpp not found at " + fn_cpp)
