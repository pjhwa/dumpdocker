#include <stdio.h>
#include <string.h>
#include <stdlib.h>

void myPrint(char *str, int a)
{
        printf("%s\n", str-a);
}

int main(int argc, char** argv)
{
        int offset = 0;

        if (argc >= 2)
                offset = atoi(argv[1]);

        char *str = (char*)malloc(100);
        strcpy(str, "Dumpdocker is a great tool for dump analysis!");
        myPrint(str, offset);

        return 0;
}
