const { CosmosStore } = require("./db.cjs");

describe("Azure Cosmos DB", () => {
  test("should able to create", async () => {
    const c = new CosmosStore(
      "http://127.0.0.1:8081",
      "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
      "db",
      "container",
    );

    const data = Buffer.from("sfsdf");
    await c.createData("hello2", data);

    const l = await c.listData();
    expect(l.length).toBeGreaterThanOrEqual(1);

    const d = await c.getData("hello2");
    console.log(d);
    expect(d).toBe(data);
  });
});
