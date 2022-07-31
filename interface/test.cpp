#include <bits/stdc++.h>

using namespace std;


int main() {
    std::ios_base::sync_with_stdio(0);
    cin.tie(0);
    cout.precision(10);

    int n;
    cin >> n;

    for (size_t i = 0; i < n; ++i) {
        string alienNumber, sourceLanguage, targetLanguage;
        cin >> alienNumber >> sourceLanguage >> targetLanguage;

        int decimalNumber = 0;

        for (const auto &digit: alienNumber) {
            if (sourceLanguage.find(digit) != string::npos) {
                decimalNumber = decimalNumber * sourceLanguage.size() + sourceLanguage.find(digit);
            } else {
                cout << "Case #" << i + 1 << ": " << "ERROR\n";
                break;
            }
        }

        string targetNumber;

        while (decimalNumber > 0) {
            targetNumber = targetLanguage[decimalNumber % targetLanguage.size()] + targetNumber;
            decimalNumber /= targetLanguage.size();
        }

        cout << "Case #" << i + 1 << ": " << targetNumber << "\n";
    }

    return 0;
}