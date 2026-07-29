#include <iostream>
#include <algorithm>
#include <fstream>
#include <chrono>

#include "rclcpp/rclcpp.hpp"
#include "stereo-inertial-node.hpp"

#include "../timing.h"
#include "System.h"

int main(int argc, char **argv)
{
    if(argc < 4)
    {
        std::cerr << "\nUsage: ros2 run orbslam stereo path_to_vocabulary path_to_settings do_rectify [do_equalize]" << std::endl;
        rclcpp::shutdown();
        return 1;
    }

    std::string do_equalize = (argc > 4) ? argv[4] : "false";

    rclcpp::init(argc, argv);
    orb_timing::TimingLogger::instance().open("/results/orbslam3_scoped_timing.csv");

    // malloc error using new.. try shared ptr
    // Create SLAM system. It initializes all system threads and gets ready to process frames.

    bool visualization = false;
    ORB_SLAM3::System pSLAM(argv[1], argv[2], ORB_SLAM3::System::IMU_STEREO, visualization);

    auto node = std::make_shared<StereoInertialNode>(&pSLAM, argv[2], argv[3], do_equalize);
    std::cout << "============================" << std::endl;

    rclcpp::spin(node);
    rclcpp::shutdown();

    return 0;
}
