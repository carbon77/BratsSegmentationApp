FROM maven:3.9.10-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn -B dependency:go-offline
COPY src ./src
RUN mvn -B package -DskipTests

FROM eclipse-temurin:21-jre
WORKDIR /app
RUN mkdir -p /app/upload-staging
COPY --from=build /app/target/brats-segmentation-backend-0.0.1-SNAPSHOT.jar /app/app.jar
EXPOSE 8000
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
