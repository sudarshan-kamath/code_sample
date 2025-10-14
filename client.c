/*
 * Simple TCP Client Example for RTLinux
 * Replace this with your actual client implementation
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>

#define BUFFER_SIZE 1024
#define NUM_MESSAGES 5

int main(int argc, char *argv[]) {
    int sock_fd;
    struct sockaddr_in server_addr;
    struct hostent *server;
    char buffer[BUFFER_SIZE];
    char message[BUFFER_SIZE];
    char *hostname;
    int port;
    int bytes_sent, bytes_received;
    int i;

    // Parse arguments
    if (argc != 3) {
        fprintf(stderr, "Usage: %s <hostname> <port>\n", argv[0]);
        return 1;
    }
    hostname = argv[1];
    port = atoi(argv[2]);

    printf("=== TCP Client Starting ===\n");
    printf("Server: %s\n", hostname);
    printf("Port: %d\n", port);
    printf("===========================\n\n");

    // Resolve hostname
    server = gethostbyname(hostname);
    if (server == NULL) {
        fprintf(stderr, "ERROR: No such host: %s\n", hostname);
        return 1;
    }

    // Create socket
    sock_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (sock_fd < 0) {
        perror("ERROR: Socket creation failed");
        return 1;
    }

    // Configure server address
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    memcpy(&server_addr.sin_addr.s_addr, server->h_addr, server->h_length);
    server_addr.sin_port = htons(port);

    // Connect to server
    printf("Connecting to server...\n");
    if (connect(sock_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("ERROR: Connection failed");
        close(sock_fd);
        return 1;
    }
    printf("Connected successfully!\n\n");

    // Send messages to server
    for (i = 1; i <= NUM_MESSAGES; i++) {
        // Create message
        snprintf(message, BUFFER_SIZE, "Message %d from client", i);

        printf("[MSG %d] Sending: %s\n", i, message);

        // Send to server
        bytes_sent = send(sock_fd, message, strlen(message), 0);
        if (bytes_sent < 0) {
            perror("ERROR: Send failed");
            break;
        }
        printf("[MSG %d] Sent %d bytes\n", i, bytes_sent);

        // Receive echo from server
        memset(buffer, 0, BUFFER_SIZE);
        bytes_received = recv(sock_fd, buffer, BUFFER_SIZE - 1, 0);
        if (bytes_received < 0) {
            perror("ERROR: Receive failed");
            break;
        }
        printf("[MSG %d] Received echo: %s (%d bytes)\n", i, buffer, bytes_received);

        // Small delay between messages
        sleep(1);
    }

    // Statistics
    printf("\n=== Client Statistics ===\n");
    printf("Messages sent: %d\n", i - 1);
    printf("========================\n");

    // Cleanup
    close(sock_fd);
    printf("Connection closed\n");

    return 0;
}
