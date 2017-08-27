LIBRARY_NAME = libhermes.a

SRCFILES = $(wildcard source/*.cpp)
OBJFILES = $(SRCFILES:%.cpp=%.o)

CXXFLAGS += -std=c++11 -fPIC -fno-strict-aliasing -fstack-protector -Iinclude -Idepend/aes/include -Idepend/curl/include -Idepend/jsoncpp/include

ifndef NDEBUG
CXXFLAGS += -g -D_DEBUG=1 -DDEBUG=1
else
CXXFLAGS += -DNDEBUG=1 -O2
endif

all: build

$(LIBRARY_NAME): $(OBJFILES)
	$(AR) rs $@ $^

build: $(LIBRARY_NAME)
	cp $^ tmp/
	rm $^

%.d:%.cpp
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -MM -MF $@ $<

ifneq ($(MAKECMDGOALS),clean)
-include $(OBJFILES:.o=.d)
endif

clean:
	$(RM) $(OBJFILES) $(OBJFILES:.o=.d)

.PHONY: all build clean
