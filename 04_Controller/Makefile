TARGET=main
SRCS = main.cpp MiniPID.cpp

all: $(TARGET)

$(TARGET): $(SRCS) Makefile
	g++ -g -Wall -std=c++11 -o $(TARGET) $(SRCS)

clean:
	$(RM) $(TARGET)

run:
	./$(TARGET)
