#include <opencv2/core/core.hpp>
#include <iostream>

int main() {
    cv::FileStorage fs;
    std::string filepath = "/suedhoehe_kimera_params/FrontendParams.yaml";
    fs.open(filepath, cv::FileStorage::READ);
    if (!fs.isOpened()) {
        std::cerr << "Failed to open file: " << filepath << std::endl;
        return -1;
    }
    std::cout << "Successfully opened file: " << filepath << std::endl;
    cv::FileNode node = fs["maxFeaturesPerFrame"];
    if (node.type() == cv::FileNode::NONE) {
        std::cerr << "maxFeaturesPerFrame is NONE!" << std::endl;
    } else {
        int val = 0;
        node >> val;
        std::cout << "maxFeaturesPerFrame = " << val << std::endl;
    }
    cv::FileNode node2 = fs["feature_detector_type"];
    if (node2.type() == cv::FileNode::NONE) {
        std::cerr << "feature_detector_type is NONE!" << std::endl;
    } else {
        int val = 0;
        node2 >> val;
        std::cout << "feature_detector_type = " << val << std::endl;
    }
    return 0;
}
