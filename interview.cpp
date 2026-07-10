#include <ros/ros.h>
#include <std_msgs/String.h>
#include <std_srvs/Empty.h>
#include <vector>
#include <iostream>
using namespace std;

void f1(int argc, char** argv)
{
    ros::init(argc, argv, "cpp_interview_node");
    ros::NodeHandle nh;
    ros::Publisher p = nh.advertise<std_msgs::String>("chatter", 1000);
    auto l = [](const std_msgs::String::ConstPtr& msg) {
        ROS_INFO("I heard: [%s]", msg->data.c_str());
    };
    ros::Subscriber s = nh.subscribe("chatter", 1000, l);
    ros::ServiceClient c = nh.serviceClient<std_srvs::Empty>("reset");
    std_srvs::Empty srv;
    ros::service::waitForService("reset", -1);
    if(c.call(srv))
        ROS_INFO("Service call successful.");
    else
        ROS_ERROR("Failed to call service 'reset'.");
    std_msgs::String m;
    m.data = "Hello, ROS!";
    p.publish(m);
    ros::spinOnce();
    ros::Duration(0.5).sleep();
}

void s1(vector<int>& v)
{
    for (size_t i = 1; i < v.size(); i++)
    {
        int key = v[i];
        int j = i - 1;
        while (j >= 0 && v[j] > key)
        {
            v[j + 1] = v[j];
            j--;
        }
        v[j + 1] = key;
    }
}

void g1(const vector<int>& v, int index, int target, vector<int>& curr)
{
    if (target == 0)
    {
        cout << "[ ";
        for (int n : curr)
            cout << n << " ";
        cout << "]" << endl;
        return;
    }
    if (index >= v.size() || target < 0)
        return;
    
    curr.push_back(v[index]);
    g1(v, index + 1, target - v[index], curr);
    curr.pop_back();
    
    g1(v, index + 1, target, curr);
}

void f3(vector<int> v, int t)
{
    vector<int> curr;
    g1(v, 0, t, curr);
}

int main(int argc, char** argv)
{
    cout << "=== f1 ===" << endl;
    f1(argc, argv);
    cout << "\n=== f3 ===" << endl;
    vector<int> arr = {1,2,3,4,5,6,7,8,9,10};
    int target = 5;
    f3(arr, target);
    return 0;
}
