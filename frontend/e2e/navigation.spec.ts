import { test, expect } from "@playwright/test";

test.describe("Navegação Principal e Links Externos", () => {
  // Antes de cada teste, navega para a página inicial.
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("deve navegar para a página de login de admin", async ({ page }) => {
    // Clica no link "Acesso Administrativo".
    await page.getByRole("link", { name: "Acesso Administrativo" }).click();

    // Verifica se a URL mudou para a página de login.
    await expect(page).toHaveURL("/admin/login");
    // Verifica se o título da página está correto.
    await expect(
      page.getByRole("heading", { name: "Acesso Administrativo" }),
    ).toBeVisible();
  });

  test("deve navegar para a documentação da API", async ({ page }) => {
    // Clica no link "Documentação da API".
    await page.getByRole("link", { name: "Documentação da API" }).click();

    // Verifica se a URL mudou para a página de documentação.
    await expect(page).toHaveURL("/apidocs");
    // Verifica se o título da página é "Flasgger", indicando que a página correta foi carregada.
    await expect(page).toHaveTitle(/Flasgger/);
  });

  test("deve navegar para a página de histórico", async ({ page }) => {
    await page.getByRole("link", { name: "Histórico de Análises" }).click();
    await expect(page).toHaveURL("/history");
    await expect(
      page.getByRole("heading", { name: "Histórico de Análises" }),
    ).toBeVisible();
  });
});
