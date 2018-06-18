#include <mcm.h>
#include <iostream>
#include <cmath>
using namespace std;

double SimpleMonteCarlo1(double Expiry, 
                         double Strike, 
                         double Spot, 
                         double Vol, 
                         double r, 
                         unsigned long NumberOfPaths)
{
    double varience = Vol * Vol * Expiry;
    double rootVarience = sqrt(varience);
    double itoCorrection = -0.5*varience;

    double movedSpot = Spot * exp(r*Expiry + itoCorrection);
    double thisSpot;
    double runningSum = 0;
    for (unsigned long i = 0; i < NumberOfPaths; i++)
    {
        double thisGaussian = GetOneGaussianByBoxMuller();
        thisSpot = movedSpot * exp(rootVariance * thisGaussian);
        double thisPayoff = thisSpot - Strike;
        thisPayoff = thisPayoff > 0 ? thisPayoff : 0;
        runningSum += thisPayoff;
    }
    double mean = runningSum / NumberOfPaths;
    mean *= exp(-r * Expiry);
    return mean;
}

int main()
{
    double Expiry;
    double Strike;
    double Spot;
    double Vol;
    double r;
    unsigned long NumberOfPaths;
    cout << "\nEnter expiry\n";
    cin >> Expiry;
    cout << "\nEnter strike\n";
    cin >> Strike;
    cout << "\nEnter spot\n";
    cin >> Spot;
    cout << "\nEnter vol\n";
    cin >> Vol;
    cout << "\nr\n";
    cin >> r;
    cout << "\nNumber of paths\n";
    cin >> NumberOfPaths;
    double result = SimpleMonteCarlo1(Expiry,
                                      Strike,
                                      Spot,
                                      Vol,
                                      r,
                                      NumberOfPaths);
    cout << "the price is " << result << "\n";
    double tmp;
    cin >> tmp;
    return 0;
}

// --> Upcoming changes
//           Give Price Puts, Price double digits.
//